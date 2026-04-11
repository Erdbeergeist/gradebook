from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.classes import Class
from app.models.exams import Exam
from app.models.grading_schemas import GradingSchema, GradingSchemaType
from app.schemas.exams import ExamCreate, ExamUpdate
from app.services import grading_schemas_service


def create_exam(
    db: Session,
    school_id: UUID,
    payload: ExamCreate,
) -> tuple[str, Exam | None]:
    class_ = db.execute(
        select(Class)
        .where(Class.id == payload.class_id)
        .where(Class.school_id == school_id)
    ).scalar_one_or_none()

    if class_ is None:
        return "class_not_found", None

    grading_schema = db.execute(
        select(GradingSchema)
        .where(GradingSchema.id == payload.template_grading_schema_id)
        .where(GradingSchema.school_id == school_id)
    ).scalar_one_or_none()

    if grading_schema is None:
        return "grading_schema_not_found", None

    if grading_schema.teacher_id != class_.teacher_id:
        return "grading_schema_teacher_mismatch", None

    if (
        grading_schema.scheme_type == GradingSchemaType.POINTS
        and payload.max_points != grading_schema.max_points
    ):
        return "points_schema_max_points_mismatch", None

    clone_result, cloned_schema = grading_schemas_service.clone_grading_schema(
        db=db,
        school_id=school_id,
        source_schema_id=grading_schema.id,
        teacher_id=class_.teacher_id,
        name=grading_schema.name,
        as_template=False,
    )

    if clone_result == "source_schema_not_found":
        return "grading_schema_not_found", None

    if clone_result in {"teacher_not_found", "source_schema_not_clonable"}:
        return "grading_schema_not_found", None

    if cloned_schema is None:
        return "grading_schema_not_found", None

    exam = Exam(
        school_id=school_id,
        class_id=payload.class_id,
        grading_schema_id=cloned_schema.id,
        name=payload.name,
        exam_type=payload.exam_type,
        exam_type_detail=payload.exam_type_detail,
        max_points=payload.max_points,
        weight=payload.weight,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return "created", exam


def get_exam(
    db: Session,
    exam_id: UUID,
    school_id: UUID,
) -> Exam | None:
    statement = (
        select(Exam).where(Exam.id == exam_id).where(Exam.school_id == school_id)
    )
    return db.execute(statement).scalar_one_or_none()


def update_exam(
    db: Session,
    school_id: UUID,
    exam_id: UUID,
    payload: ExamUpdate,
) -> tuple[str, Exam | None]:
    exam = db.execute(
        select(Exam).where(Exam.id == exam_id).where(Exam.school_id == school_id)
    ).scalar_one_or_none()

    if exam is None:
        return "exam_not_found", None

    grading_schema = db.execute(
        select(GradingSchema)
        .where(GradingSchema.id == exam.grading_schema_id)
        .where(GradingSchema.school_id == school_id)
    ).scalar_one_or_none()

    if grading_schema is None:
        return "grading_schema_not_found", None

    if (
        grading_schema.scheme_type == GradingSchemaType.POINTS
        and payload.max_points != grading_schema.max_points
    ):
        return "points_schema_max_points_mismatch", None

    exam.name = payload.name
    exam.exam_type = payload.exam_type
    exam.exam_type_detail = payload.exam_type_detail
    exam.max_points = payload.max_points
    exam.weight = payload.weight

    db.commit()
    db.refresh(exam)
    return "updated", exam


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
