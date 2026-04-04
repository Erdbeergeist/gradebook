from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.students import Student
from app.schemas.students import StudentCreate


def create_student(
    db: Session,
    school_id: UUID,
    payload: StudentCreate,
) -> Student:
    student = Student(
        school_id=school_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def get_student(
    db: Session,
    student_id: UUID,
    school_id: UUID,
) -> Student | None:
    statement = (
        select(Student)
        .where(Student.id == student_id)
        .where(Student.school_id == school_id)
    )
    return db.execute(statement).scalar_one_or_none()


def list_students(
    db: Session,
    school_id: UUID,
) -> list[Student]:
    statement = (
        select(Student)
        .where(Student.school_id == school_id)
        .order_by(Student.created_at.asc())
    )
    return list(db.execute(statement).scalars().all())
