from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session, selectinload
from collections import Counter
from uuid import UUID

from app.models.classes import Class
from app.models.teachers import Teacher
from app.models.enrollments import Enrollment
from app.models.exams import Exam
from app.models.students import Student
from app.models.exam_results import ExamResult
from app.schemas.classes import (
    ClassCreate,
    ClassGradebookRead,
    ClassRead,
    GradebookCellRead,
    GradebookExamRead,
    GradebookStudentRead,
    ClassGradebookBulkUpsertRequest,
)
from app.schemas.exam_results import ExamResultRead
from app.services.exam_results_service import (
    _exam_result_load_options,
    _to_exam_result_read,
)


def create_class(
    db: Session,
    school_id: UUID,
    payload: ClassCreate,
) -> Class | None:
    teacher = db.execute(
        select(Teacher)
        .where(Teacher.id == payload.teacher_id)
        .where(Teacher.school_id == school_id)
    ).scalar_one_or_none()

    if teacher is None:
        return None

    class_ = Class(
        school_id=school_id,
        teacher_id=payload.teacher_id,
        name=payload.name,
    )
    db.add(class_)
    db.commit()
    db.refresh(class_)
    return class_


def get_class(
    db: Session,
    class_id: UUID,
    school_id: UUID,
) -> Class | None:
    statement = (
        select(Class).where(Class.id == class_id).where(Class.school_id == school_id)
    )
    return db.execute(statement).scalar_one_or_none()


def list_classes(
    db: Session,
    school_id: UUID,
    teacher_id: UUID | None = None,
) -> list[Class]:
    statement = select(Class).where(Class.school_id == school_id)

    if teacher_id is not None:
        statement = statement.where(Class.teacher_id == teacher_id)

    statement = statement.order_by(Class.created_at.asc())

    return list(db.execute(statement).scalars().all())


def get_class_gradebook(
    db: Session,
    class_id: UUID,
    school_id: UUID,
) -> ClassGradebookRead | None:
    class_statement = (
        select(Class)
        .options(
            selectinload(Class.enrollments).joinedload(Enrollment.student),
            selectinload(Class.exams),
        )
        .where(Class.id == class_id)
        .where(Class.school_id == school_id)
    )
    class_ = db.execute(class_statement).scalar_one_or_none()

    if class_ is None:
        return None

    students = sorted(
        [enrollment.student for enrollment in class_.enrollments],
        key=lambda student: (
            student.last_name.casefold(),
            student.first_name.casefold(),
            str(student.id),
        ),
    )

    exams = sorted(
        list(class_.exams),
        key=lambda exam: (exam.created_at, str(exam.id)),
    )

    exam_ids = [exam.id for exam in exams]

    exam_result_reads_by_pair: dict[tuple[UUID, UUID], ExamResultRead] = {}

    if exam_ids:
        exam_results_statement = (
            select(ExamResult)
            .options(*_exam_result_load_options())
            .join(Exam, ExamResult.exam_id == Exam.id)
            .join(Student, ExamResult.student_id == Student.id)
            .where(Exam.class_id == class_.id)
            .where(Exam.school_id == school_id)
            .where(Student.school_id == school_id)
            .order_by(ExamResult.created_at.asc())
        )
        exam_results = list(db.execute(exam_results_statement).scalars().all())

        for exam_result in exam_results:
            exam_result_read = _to_exam_result_read(exam_result)
            exam_result_reads_by_pair[
                (exam_result_read.student_id, exam_result_read.exam_id)
            ] = exam_result_read

    cells: list[GradebookCellRead] = []
    for student in students:
        for exam in exams:
            exam_result_read = exam_result_reads_by_pair.get((student.id, exam.id))
            if exam_result_read is None:
                cells.append(
                    GradebookCellRead(
                        student_id=student.id,
                        exam_id=exam.id,
                        exam_result_id=None,
                        points=None,
                        comment=None,
                        status=None,
                        graded_at=None,
                        resolved_input_value=None,
                        resolved_grade_label=None,
                    )
                )
            else:
                cells.append(
                    GradebookCellRead(
                        student_id=student.id,
                        exam_id=exam.id,
                        exam_result_id=exam_result_read.id,
                        points=exam_result_read.points,
                        comment=exam_result_read.comment,
                        status=exam_result_read.status,
                        graded_at=exam_result_read.graded_at,
                        resolved_input_value=exam_result_read.resolved_input_value,
                        resolved_grade_label=exam_result_read.resolved_grade_label,
                    )
                )

    return ClassGradebookRead(
        class_=ClassRead.model_validate(class_),
        students=[GradebookStudentRead.model_validate(student) for student in students],
        exams=[GradebookExamRead.model_validate(exam) for exam in exams],
        cells=cells,
    )


def bulk_upsert_class_gradebook_results(
    db: Session,
    school_id: UUID,
    class_id: UUID,
    payload: ClassGradebookBulkUpsertRequest,
) -> tuple[str, list[ExamResultRead] | None]:
    class_ = db.execute(
        select(Class).where(Class.id == class_id).where(Class.school_id == school_id)
    ).scalar_one_or_none()
    if class_ is None:
        return "class_not_found", None

    pair_counts = Counter((item.exam_id, item.student_id) for item in payload.items)
    duplicate_pairs = [pair for pair, count in pair_counts.items() if count > 1]
    if duplicate_pairs:
        return "duplicate_pairs_in_payload", None

    exam_ids = sorted({item.exam_id for item in payload.items}, key=str)
    student_ids = sorted({item.student_id for item in payload.items}, key=str)

    exams = list(
        db.execute(
            select(Exam)
            .where(Exam.id.in_(exam_ids))
            .where(Exam.school_id == school_id)
            .where(Exam.class_id == class_id)
        )
        .scalars()
        .all()
    )
    exams_by_id = {exam.id: exam for exam in exams}
    if len(exams_by_id) != len(exam_ids):
        return "exam_not_in_class", None

    students = list(
        db.execute(
            select(Student)
            .where(Student.id.in_(student_ids))
            .where(Student.school_id == school_id)
        )
        .scalars()
        .all()
    )
    students_by_id = {student.id: student for student in students}
    if len(students_by_id) != len(student_ids):
        return "student_not_found", None

    enrolled_student_ids = set(
        db.execute(
            select(Enrollment.student_id)
            .where(Enrollment.class_id == class_id)
            .where(Enrollment.student_id.in_(student_ids))
        )
        .scalars()
        .all()
    )
    if enrolled_student_ids != set(student_ids):
        return "student_not_enrolled", None

    for item in payload.items:
        exam = exams_by_id[item.exam_id]
        if item.points is not None and item.points > exam.max_points:
            return "points_exceed_max", None

    existing_results = list(
        db.execute(
            select(ExamResult).where(
                tuple_(ExamResult.exam_id, ExamResult.student_id).in_(
                    [(item.exam_id, item.student_id) for item in payload.items]
                )
            )
        )
        .scalars()
        .all()
    )
    existing_by_pair = {
        (result.exam_id, result.student_id): result for result in existing_results
    }

    touched_ids: list[UUID] = []

    for item in payload.items:
        pair = (item.exam_id, item.student_id)
        existing = existing_by_pair.get(pair)

        if existing is None:
            new_result = ExamResult(
                exam_id=item.exam_id,
                student_id=item.student_id,
                points=item.points,
                comment=item.comment,
                status=item.status,
                graded_at=item.graded_at,
            )
            db.add(new_result)
            db.flush()
            touched_ids.append(new_result.id)
        else:
            existing.points = item.points
            existing.comment = item.comment
            existing.status = item.status
            existing.graded_at = item.graded_at
            touched_ids.append(existing.id)

    db.commit()

    touched_results = list(
        db.execute(
            select(ExamResult)
            .options(*_exam_result_load_options())
            .where(ExamResult.id.in_(touched_ids))
        )
        .scalars()
        .all()
    )
    touched_by_id = {result.id: result for result in touched_results}

    return "upserted", [
        _to_exam_result_read(touched_by_id[result_id]) for result_id in touched_ids
    ]
