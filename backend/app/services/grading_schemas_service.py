from __future__ import annotations

from collections import Counter
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.grade_catalogs import GradeCatalog
from app.models.grading_schemas import (
    GradingSchema,
    GradingSchemaGrade,
    GradingSchemaOverride,
    GradingSchemaRange,
    GradingSchemaType,
)
from app.models.teachers import Teacher
from app.schemas.grading_schemas import GradingSchemaCreate, GradingSchemaUpdate


GradingSchemaPayload = GradingSchemaCreate | GradingSchemaUpdate


def _grading_schema_load_options():
    return (
        selectinload(GradingSchema.grades),
        selectinload(GradingSchema.ranges),
        selectinload(GradingSchema.overrides),
    )


def _domain_upper_bound(payload: GradingSchemaPayload) -> Decimal:
    if payload.scheme_type == GradingSchemaType.PERCENTAGE:
        return Decimal("100.00")
    return payload.max_points  # type: ignore[return-value]


def _validate_grade_inputs(
    labels: list[str],
    sort_orders: list[int],
) -> str | None:
    label_counts = Counter(labels)
    duplicate_labels = [label for label, count in label_counts.items() if count > 1]
    if duplicate_labels:
        return "duplicate_grade_labels"

    order_counts = Counter(sort_orders)
    duplicate_orders = [order for order, count in order_counts.items() if count > 1]
    if duplicate_orders:
        return "duplicate_grade_sort_orders"

    return None


def _validate_range_and_override_inputs(
    payload: GradingSchemaPayload,
    labels: set[str],
) -> str | None:
    upper = _domain_upper_bound(payload)

    for rule in payload.ranges:
        if rule.grade_label not in labels:
            return "unknown_range_grade_label"
        if rule.min_value < 0 or rule.max_value > upper:
            return "range_out_of_domain"

    seen_overrides: set[Decimal] = set()
    for item in payload.overrides:
        if item.grade_label not in labels:
            return "unknown_override_grade_label"
        if item.input_value < 0 or item.input_value > upper:
            return "override_out_of_domain"
        if item.input_value in seen_overrides:
            return "duplicate_override_input_values"
        seen_overrides.add(item.input_value)

    numeric_ranges = sorted(
        payload.ranges,
        key=lambda item: (item.min_value, item.max_value),
    )
    for left, right in zip(numeric_ranges, numeric_ranges[1:]):
        if left.max_value > right.min_value:
            return "overlapping_ranges"
        if (
            left.max_value == right.min_value
            and left.max_inclusive
            and right.min_inclusive
        ):
            return "overlapping_ranges"

    return None


def _resolve_grade_inputs(
    db: Session,
    payload: GradingSchemaPayload,
) -> tuple[str | None, list[tuple[str, int]] | None]:
    catalog = None
    if payload.grade_catalog_code is not None:
        catalog = db.execute(
            select(GradeCatalog)
            .options(selectinload(GradeCatalog.items))
            .where(GradeCatalog.code == payload.grade_catalog_code)
        ).scalar_one_or_none()
        if catalog is None:
            return "grade_catalog_not_found", None

    if catalog is not None:
        grade_inputs = [(item.label, item.sort_order) for item in catalog.items]
    else:
        grade_inputs = [(item.label, item.sort_order) for item in payload.grades]

    return None, grade_inputs


def create_grading_schema(
    db: Session,
    school_id: UUID,
    payload: GradingSchemaCreate,
) -> tuple[str, GradingSchema | None]:
    teacher = db.execute(
        select(Teacher)
        .where(Teacher.id == payload.teacher_id)
        .where(Teacher.school_id == school_id)
    ).scalar_one_or_none()
    if teacher is None:
        return "teacher_not_found", None

    error, grade_inputs = _resolve_grade_inputs(db=db, payload=payload)
    if error is not None:
        return error, None
    assert grade_inputs is not None

    labels = [label for label, _ in grade_inputs]
    sort_orders = [sort_order for _, sort_order in grade_inputs]

    error = _validate_grade_inputs(labels=labels, sort_orders=sort_orders)
    if error is not None:
        return error, None

    error = _validate_range_and_override_inputs(payload=payload, labels=set(labels))
    if error is not None:
        return error, None

    grading_schema = GradingSchema(
        school_id=school_id,
        teacher_id=payload.teacher_id,
        name=payload.name,
        scheme_type=payload.scheme_type,
        max_points=payload.max_points,
    )
    db.add(grading_schema)
    db.flush()

    grade_rows = []
    for label, sort_order in grade_inputs:
        grade = GradingSchemaGrade(
            grading_schema_id=grading_schema.id,
            label=label,
            sort_order=sort_order,
        )
        db.add(grade)
        grade_rows.append(grade)

    db.flush()

    grade_by_label = {item.label: item for item in grade_rows}

    db.add_all(
        [
            GradingSchemaRange(
                grading_schema_id=grading_schema.id,
                grade_id=grade_by_label[item.grade_label].id,
                min_value=item.min_value,
                max_value=item.max_value,
                min_inclusive=item.min_inclusive,
                max_inclusive=item.max_inclusive,
            )
            for item in payload.ranges
        ]
    )
    db.add_all(
        [
            GradingSchemaOverride(
                grading_schema_id=grading_schema.id,
                grade_id=grade_by_label[item.grade_label].id,
                input_value=item.input_value,
            )
            for item in payload.overrides
        ]
    )

    db.commit()

    grading_schema = db.execute(
        select(GradingSchema)
        .options(*_grading_schema_load_options())
        .where(GradingSchema.id == grading_schema.id)
    ).scalar_one()

    return "created", grading_schema


def get_grading_schema(
    db: Session,
    school_id: UUID,
    grading_schema_id: UUID,
) -> GradingSchema | None:
    statement = (
        select(GradingSchema)
        .options(*_grading_schema_load_options())
        .where(GradingSchema.id == grading_schema_id)
        .where(GradingSchema.school_id == school_id)
    )
    return db.execute(statement).scalar_one_or_none()


def list_grading_schemas(
    db: Session,
    school_id: UUID,
    teacher_id: UUID | None = None,
) -> list[GradingSchema]:
    statement = (
        select(GradingSchema)
        .options(*_grading_schema_load_options())
        .where(GradingSchema.school_id == school_id)
        .order_by(GradingSchema.created_at.asc())
    )
    if teacher_id is not None:
        statement = statement.where(GradingSchema.teacher_id == teacher_id)

    return list(db.execute(statement).scalars().all())


def list_grade_catalogs(db: Session):
    statement = (
        select(GradeCatalog)
        .options(selectinload(GradeCatalog.items))
        .order_by(GradeCatalog.created_at.asc())
    )
    return list(db.execute(statement).scalars().all())


def is_system_schema(schema: GradingSchema) -> bool:
    return schema.is_system


def is_template_schema(schema: GradingSchema) -> bool:
    return schema.is_template


def is_exam_schema(schema: GradingSchema) -> bool:
    return not schema.is_template


def can_edit_schema(schema: GradingSchema) -> bool:
    return not schema.is_system


def can_delete_schema(schema: GradingSchema) -> bool:
    return schema.is_template and not schema.is_system


def can_clone_schema(schema: GradingSchema) -> bool:
    return True


def can_promote_schema_to_template(schema: GradingSchema) -> bool:
    return not schema.is_template and not schema.is_system


def can_replace_template(
    target_schema: GradingSchema,
    source_schema: GradingSchema,
) -> bool:
    return (
        target_schema.is_template
        and not target_schema.is_system
        and not source_schema.is_system
    )


def clone_grading_schema(
    db: Session,
    *,
    school_id: UUID,
    source_schema_id: UUID,
    teacher_id: UUID,
    name: str | None = None,
    as_template: bool = False,
) -> tuple[str, GradingSchema | None]:
    source_schema = db.execute(
        select(GradingSchema)
        .options(*_grading_schema_load_options())
        .where(GradingSchema.id == source_schema_id)
        .where(GradingSchema.school_id == school_id)
    ).scalar_one_or_none()

    if source_schema is None:
        return "source_schema_not_found", None

    if not can_clone_schema(source_schema):
        return "source_schema_not_clonable", None

    teacher = db.execute(
        select(Teacher)
        .where(Teacher.id == teacher_id)
        .where(Teacher.school_id == school_id)
    ).scalar_one_or_none()
    if teacher is None:
        return "teacher_not_found", None

    cloned_schema = GradingSchema(
        school_id=school_id,
        teacher_id=teacher_id,
        name=name if name is not None else source_schema.name,
        scheme_type=source_schema.scheme_type,
        max_points=source_schema.max_points,
        is_active=source_schema.is_active,
        is_template=as_template,
        is_system=False,
        source_schema_id=source_schema.id,
    )
    db.add(cloned_schema)
    db.flush()

    old_grade_id_to_new_grade_id: dict[UUID, UUID] = {}

    for source_grade in source_schema.grades:
        cloned_grade = GradingSchemaGrade(
            grading_schema_id=cloned_schema.id,
            label=source_grade.label,
            sort_order=source_grade.sort_order,
        )
        db.add(cloned_grade)
        db.flush()
        old_grade_id_to_new_grade_id[source_grade.id] = cloned_grade.id

    for source_range in source_schema.ranges:
        cloned_range = GradingSchemaRange(
            grading_schema_id=cloned_schema.id,
            grade_id=old_grade_id_to_new_grade_id[source_range.grade_id],
            min_value=source_range.min_value,
            max_value=source_range.max_value,
            min_inclusive=source_range.min_inclusive,
            max_inclusive=source_range.max_inclusive,
        )
        db.add(cloned_range)

    for source_override in source_schema.overrides:
        cloned_override = GradingSchemaOverride(
            grading_schema_id=cloned_schema.id,
            grade_id=old_grade_id_to_new_grade_id[source_override.grade_id],
            input_value=source_override.input_value,
        )
        db.add(cloned_override)

    db.commit()

    cloned_schema = db.execute(
        select(GradingSchema)
        .options(*_grading_schema_load_options())
        .where(GradingSchema.id == cloned_schema.id)
    ).scalar_one()

    return "created", cloned_schema


def update_grading_schema(
    db: Session,
    school_id: UUID,
    grading_schema_id: UUID,
    payload: GradingSchemaUpdate,
) -> tuple[str, GradingSchema | None]:
    grading_schema = db.execute(
        select(GradingSchema)
        .options(*_grading_schema_load_options())
        .where(GradingSchema.id == grading_schema_id)
        .where(GradingSchema.school_id == school_id)
    ).scalar_one_or_none()

    if grading_schema is None:
        return "grading_schema_not_found", None

    if not can_edit_schema(grading_schema):
        return "grading_schema_not_editable", None

    error, grade_inputs = _resolve_grade_inputs(db=db, payload=payload)
    if error is not None:
        return error, None
    assert grade_inputs is not None

    labels = [label for label, _ in grade_inputs]
    sort_orders = [sort_order for _, sort_order in grade_inputs]

    error = _validate_grade_inputs(labels=labels, sort_orders=sort_orders)
    if error is not None:
        return error, None

    error = _validate_range_and_override_inputs(payload=payload, labels=set(labels))
    if error is not None:
        return error, None

    grading_schema.name = payload.name
    grading_schema.scheme_type = payload.scheme_type
    grading_schema.max_points = payload.max_points

    for item in list(grading_schema.ranges):
        db.delete(item)
    for item in list(grading_schema.overrides):
        db.delete(item)
    for item in list(grading_schema.grades):
        db.delete(item)

    db.flush()

    new_grades = []
    for label, sort_order in grade_inputs:
        grade = GradingSchemaGrade(
            grading_schema_id=grading_schema.id,
            label=label,
            sort_order=sort_order,
        )
        db.add(grade)
        new_grades.append(grade)

    db.flush()

    grade_by_label = {item.label: item for item in new_grades}

    db.add_all(
        [
            GradingSchemaRange(
                grading_schema_id=grading_schema.id,
                grade_id=grade_by_label[item.grade_label].id,
                min_value=item.min_value,
                max_value=item.max_value,
                min_inclusive=item.min_inclusive,
                max_inclusive=item.max_inclusive,
            )
            for item in payload.ranges
        ]
    )
    db.add_all(
        [
            GradingSchemaOverride(
                grading_schema_id=grading_schema.id,
                grade_id=grade_by_label[item.grade_label].id,
                input_value=item.input_value,
            )
            for item in payload.overrides
        ]
    )

    db.commit()

    db.expire(grading_schema, ["grades", "ranges", "overrides"])

    grading_schema = db.execute(
        select(GradingSchema)
        .execution_options(populate_existing=True)
        .options(*_grading_schema_load_options())
        .where(GradingSchema.id == grading_schema.id)
    ).scalar_one()

    return "updated", grading_schema
