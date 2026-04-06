from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.classes import Class
from app.models.enrollments import Enrollment
from app.models.exam_results import ExamResult
from app.models.exams import Exam
from app.models.students import Student
from app.schemas.exam_results import ExamResultCreate


def create_exam_result(
    db: Session,
    school_id,
    payload: ExamResultCreate,
) -> tuple[str, ExamResult | None]:
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
    db.refresh(exam_result)
    return "created", exam_result


def get_exam_result(db: Session, school_id, exam_result_id):
    statement = (
        select(ExamResult)
        .join(Exam, ExamResult.exam_id == Exam.id)
        .join(Student, ExamResult.student_id == Student.id)
        .where(ExamResult.id == exam_result_id)
        .where(Exam.school_id == school_id)
        .where(Student.school_id == school_id)
    )
    return db.execute(statement).scalar_one_or_none()


def list_exam_results_for_exam(db: Session, school_id, exam_id):
    statement = (
        select(ExamResult)
        .join(Exam, ExamResult.exam_id == Exam.id)
        .where(ExamResult.exam_id == exam_id)
        .where(Exam.school_id == school_id)
        .order_by(ExamResult.created_at.asc())
    )
    return list(db.execute(statement).scalars().all())


def list_exam_results_for_student(db: Session, school_id, student_id):
    statement = (
        select(ExamResult)
        .join(Exam, ExamResult.exam_id == Exam.id)
        .join(Student, ExamResult.student_id == Student.id)
        .where(ExamResult.student_id == student_id)
        .where(Exam.school_id == school_id)
        .where(Student.school_id == school_id)
        .order_by(ExamResult.created_at.asc())
    )
    return list(db.execute(statement).scalars().all())


def delete_exam_result(db: Session, school_id, exam_result_id):
    exam_result = get_exam_result(
        db=db,
        school_id=school_id,
        exam_result_id=exam_result_id,
    )
    if exam_result is None:
        return None

    db.delete(exam_result)
    db.commit()
    return exam_result
