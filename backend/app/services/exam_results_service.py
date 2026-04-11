from __future__ import annotations

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.classes import Class
from app.models.enrollments import Enrollment
from app.models.exam_results import ExamResult
from app.models.exams import Exam
from app.models.grading_schemas import (
    GradingSchema,
    GradingSchemaOverride,
    GradingSchemaRange,
)
from app.models.students import Student
from app.schemas.exam_results import ExamResultCreate, ExamResultRead, ExamResultUpdate
from app.services.grading_engine import resolve_grade_for_exam_result


def _exam_result_load_options():
    return (
        joinedload(ExamResult.exam)
        .joinedload(Exam.grading_schema)
        .selectinload(GradingSchema.ranges)
        .joinedload(GradingSchemaRange.grade),
        joinedload(ExamResult.exam)
        .joinedload(Exam.grading_schema)
        .selectinload(GradingSchema.overrides)
        .joinedload(GradingSchemaOverride.grade),
    )


def _to_exam_result_read(exam_result: ExamResult) -> ExamResultRead:
    exam = exam_result.exam
    grading_schema = exam.grading_schema

    resolved_input_value, resolved_grade_label = resolve_grade_for_exam_result(
        exam=exam,
        grading_schema=grading_schema,
        exam_result=exam_result,
    )

    return ExamResultRead(
        id=exam_result.id,
        exam_id=exam_result.exam_id,
        student_id=exam_result.student_id,
        points=exam_result.points,
        comment=exam_result.comment,
        status=exam_result.status,
        graded_at=exam_result.graded_at,
        resolved_input_value=resolved_input_value,
        resolved_grade_label=resolved_grade_label,
        created_at=exam_result.created_at,
        updated_at=exam_result.updated_at,
    )


def create_exam_result(
    db: Session,
    school_id,
    payload: ExamResultCreate,
) -> tuple[str, ExamResultRead | None]:
    exam = db.execute(
        select(Exam)
        .where(Exam.id == payload.exam_id)
        .where(Exam.school_id == school_id)
    ).scalar_one_or_none()
    if exam is None:
        return "exam_not_found", None

    student = db.execute(
        select(Student)
        .where(Student.id == payload.student_id)
        .where(Student.school_id == school_id)
    ).scalar_one_or_none()
    if student is None:
        return "student_not_found", None

    enrollment = db.execute(
        select(Enrollment)
        .join(Class, Enrollment.class_id == Class.id)
        .where(Enrollment.class_id == exam.class_id)
        .where(Enrollment.student_id == payload.student_id)
        .where(Class.school_id == school_id)
    ).scalar_one_or_none()
    if enrollment is None:
        return "student_not_enrolled", None

    existing = db.execute(
        select(ExamResult)
        .where(ExamResult.exam_id == payload.exam_id)
        .where(ExamResult.student_id == payload.student_id)
    ).scalar_one_or_none()
    if existing is not None:
        return "duplicate", None

    if payload.points is not None and payload.points > exam.max_points:
        return "points_exceed_max", None

    exam_result = ExamResult(
        exam_id=payload.exam_id,
        student_id=payload.student_id,
        points=payload.points,
        comment=payload.comment,
        status=payload.status,
        graded_at=payload.graded_at,
    )
    db.add(exam_result)
    db.commit()

    statement = (
        select(ExamResult)
        .options(*_exam_result_load_options())
        .where(ExamResult.id == exam_result.id)
    )
    created = db.execute(statement).scalar_one()
    return "created", _to_exam_result_read(created)


def update_exam_result(
    db: Session,
    school_id: UUID,
    exam_result_id: UUID,
    payload: ExamResultUpdate,
) -> tuple[str, ExamResultRead | None]:
    statement = (
        select(ExamResult)
        .join(Exam, ExamResult.exam_id == Exam.id)
        .join(Student, ExamResult.student_id == Student.id)
        .where(ExamResult.id == exam_result_id)
        .where(Exam.school_id == school_id)
        .where(Student.school_id == school_id)
    )
    exam_result = db.execute(statement).scalar_one_or_none()

    if exam_result is None:
        return "exam_result_not_found", None

    exam = db.execute(
        select(Exam)
        .where(Exam.id == exam_result.exam_id)
        .where(Exam.school_id == school_id)
    ).scalar_one()

    if payload.points is not None and payload.points > exam.max_points:
        return "points_exceed_max", None

    exam_result.points = payload.points
    exam_result.comment = payload.comment
    exam_result.status = payload.status
    exam_result.graded_at = payload.graded_at

    db.commit()
    exam_result = db.execute(
        select(ExamResult)
        .options(joinedload(ExamResult.exam).joinedload(Exam.grading_schema))
        .join(Exam, ExamResult.exam_id == Exam.id)
        .join(Student, ExamResult.student_id == Student.id)
        .where(ExamResult.id == exam_result_id)
        .where(Exam.school_id == school_id)
        .where(Student.school_id == school_id)
    ).scalar_one()

    return "updated", _to_exam_result_read(exam_result)


def get_exam_result(db: Session, school_id, exam_result_id) -> ExamResultRead | None:
    statement = (
        select(ExamResult)
        .options(*_exam_result_load_options())
        .join(Exam, ExamResult.exam_id == Exam.id)
        .join(Student, ExamResult.student_id == Student.id)
        .where(ExamResult.id == exam_result_id)
        .where(Exam.school_id == school_id)
        .where(Student.school_id == school_id)
    )
    exam_result = db.execute(statement).scalar_one_or_none()
    if exam_result is None:
        return None

    return _to_exam_result_read(exam_result)


def list_exam_results_for_exam(db: Session, school_id, exam_id) -> list[ExamResultRead]:
    statement = (
        select(ExamResult)
        .options(*_exam_result_load_options())
        .join(Exam, ExamResult.exam_id == Exam.id)
        .where(ExamResult.exam_id == exam_id)
        .where(Exam.school_id == school_id)
        .order_by(ExamResult.created_at.asc())
    )
    exam_results = list(db.execute(statement).scalars().all())
    return [_to_exam_result_read(item) for item in exam_results]


def list_exam_results_for_student(
    db: Session, school_id, student_id
) -> list[ExamResultRead]:
    statement = (
        select(ExamResult)
        .options(*_exam_result_load_options())
        .join(Exam, ExamResult.exam_id == Exam.id)
        .join(Student, ExamResult.student_id == Student.id)
        .where(ExamResult.student_id == student_id)
        .where(Exam.school_id == school_id)
        .where(Student.school_id == school_id)
        .order_by(ExamResult.created_at.asc())
    )
    exam_results = list(db.execute(statement).scalars().all())
    return [_to_exam_result_read(item) for item in exam_results]


def delete_exam_result(db: Session, school_id, exam_result_id) -> ExamResultRead | None:
    statement = (
        select(ExamResult)
        .options(*_exam_result_load_options())
        .join(Exam, ExamResult.exam_id == Exam.id)
        .join(Student, ExamResult.student_id == Student.id)
        .where(ExamResult.id == exam_result_id)
        .where(Exam.school_id == school_id)
        .where(Student.school_id == school_id)
    )
    exam_result = db.execute(statement).scalar_one_or_none()
    if exam_result is None:
        return None

    response_model = _to_exam_result_read(exam_result)
    db.delete(exam_result)
    db.commit()
    return response_model
