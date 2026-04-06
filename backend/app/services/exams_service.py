from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.classes import Class
from app.models.exams import Exam
from app.schemas.exams import ExamCreate


def create_exam(
    db: Session,
    school_id: UUID,
    payload: ExamCreate,
) -> Exam | None:
    class_ = db.execute(
        select(Class)
        .where(Class.id == payload.class_id)
        .where(Class.school_id == school_id)
    ).scalar_one_or_none()

    if class_ is None:
        return None

    exam = Exam(
        school_id=school_id,
        class_id=payload.class_id,
        name=payload.name,
        exam_type=payload.exam_type,
        exam_type_detail=payload.exam_type_detail,
        max_points=payload.max_points,
        weight=payload.weight,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


def get_exam(
    db: Session,
    exam_id: UUID,
    school_id: UUID,
) -> Exam | None:
    statement = (
        select(Exam).where(Exam.id == exam_id).where(Exam.school_id == school_id)
    )
    return db.execute(statement).scalar_one_or_none()


def list_exams(
    db: Session,
    school_id: UUID,
    class_id: UUID | None = None,
    teacher_id: UUID | None = None,
) -> list[Exam]:
    statement = select(Exam).where(Exam.school_id == school_id)

    if teacher_id is not None:
        statement = statement.join(Class, Exam.class_id == Class.id).where(
            Class.teacher_id == teacher_id
        )

    if class_id is not None:
        statement = statement.where(Exam.class_id == class_id)

    statement = statement.order_by(Exam.created_at.asc())

    return list(db.execute(statement).scalars().all())
