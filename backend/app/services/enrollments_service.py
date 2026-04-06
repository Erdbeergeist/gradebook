from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.classes import Class
from app.models.enrollments import Enrollment
from app.models.students import Student
from app.schemas.enrollments import EnrollmentCreate


def create_enrollment(
    db: Session,
    school_id: UUID,
    payload: EnrollmentCreate,
) -> Enrollment | None:
    class_ = db.execute(
        select(Class)
        .where(Class.id == payload.class_id)
        .where(Class.school_id == school_id)
    ).scalar_one_or_none()
    if class_ is None:
        return None

    student = db.execute(
        select(Student)
        .where(Student.id == payload.student_id)
        .where(Student.school_id == school_id)
    ).scalar_one_or_none()
    if student is None:
        return None

    enrollment = db.execute(
        select(Enrollment)
        .where(Enrollment.class_id == payload.class_id)
        .where(Enrollment.student_id == payload.student_id)
    ).scalar_one_or_none()
    if enrollment is not None:
        return enrollment

    enrollment = Enrollment(
        class_id=payload.class_id,
        student_id=payload.student_id,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def get_enrollment(
    db: Session,
    enrollment_id: UUID,
    school_id: UUID,
) -> Enrollment | None:
    statement = (
        select(Enrollment)
        .join(Class, Enrollment.class_id == Class.id)
        .join(Student, Enrollment.student_id == Student.id)
        .where(Enrollment.id == enrollment_id)
        .where(Class.school_id == school_id)
        .where(Student.school_id == school_id)
    )
    return db.execute(statement).scalar_one_or_none()


def list_enrollments_for_class(
    db: Session,
    class_id: UUID,
    school_id: UUID,
) -> list[Enrollment]:
    statement = (
        select(Enrollment)
        .join(Class, Enrollment.class_id == Class.id)
        .join(Student, Enrollment.student_id == Student.id)
        .where(Enrollment.class_id == class_id)
        .where(Class.school_id == school_id)
        .where(Student.school_id == school_id)
        .order_by(Enrollment.created_at.asc())
    )
    return list(db.execute(statement).scalars().all())


def list_enrollments_for_student(
    db: Session,
    student_id: UUID,
    school_id: UUID,
) -> list[Enrollment]:
    statement = (
        select(Enrollment)
        .join(Class, Enrollment.class_id == Class.id)
        .join(Student, Enrollment.student_id == Student.id)
        .where(Enrollment.student_id == student_id)
        .where(Class.school_id == school_id)
        .where(Student.school_id == school_id)
        .order_by(Enrollment.created_at.asc())
    )
    return list(db.execute(statement).scalars().all())


def delete_enrollment(
    db: Session,
    enrollment_id: UUID,
    school_id: UUID,
) -> Enrollment | None:
    enrollment = db.execute(
        select(Enrollment)
        .join(Class, Enrollment.class_id == Class.id)
        .join(Student, Enrollment.student_id == Student.id)
        .where(Enrollment.id == enrollment_id)
        .where(Class.school_id == school_id)
        .where(Student.school_id == school_id)
    ).scalar_one_or_none()
    if enrollment is None:
        return None

    db.delete(enrollment)
    db.commit()
    return enrollment
