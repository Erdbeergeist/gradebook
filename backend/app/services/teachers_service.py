from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.teachers import Teacher
from app.schemas.teachers import TeacherCreate


def create_teacher(
    db: Session,
    school_id: UUID,
    payload: TeacherCreate,
) -> Teacher:
    teacher = Teacher(
        school_id=school_id,
        name=payload.name,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


def get_teacher(
    db: Session,
    teacher_id: UUID,
    school_id: UUID,
) -> Teacher | None:
    statement = (
        select(Teacher)
        .where(Teacher.id == teacher_id)
        .where(Teacher.school_id == school_id)
    )
    return db.execute(statement).scalar_one_or_none()


def list_teachers(
    db: Session,
    school_id: UUID,
) -> list[Teacher]:
    statement = (
        select(Teacher)
        .where(Teacher.school_id == school_id)
        .order_by(Teacher.created_at.asc())
    )
    return list(db.execute(statement).scalars().all())
