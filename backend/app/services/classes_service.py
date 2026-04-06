from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.classes import Class
from app.models.teachers import Teacher
from app.schemas.classes import ClassCreate


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
