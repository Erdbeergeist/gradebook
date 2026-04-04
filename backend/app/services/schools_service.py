from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.schools import School
from app.schemas.schools import SchoolCreate


def create_school(db: Session, payload: SchoolCreate) -> School:
    school = School(name=payload.name)
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def get_school(db: Session, school_id: UUID) -> School | None:
    statement = select(School).where(School.id == school_id)
    return db.execute(statement).scalar_one_or_none()


def list_schools(db: Session) -> list[School]:
    statement = select(School).order_by(School.created_at.asc())
    return list(db.execute(statement).scalars().all())
