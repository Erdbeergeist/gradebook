from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.grading_schemas import (
    GradingSchema,
    GradingSchemaGrade,
    GradingSchemaOverride,
    GradingSchemaRange,
    GradingSchemaType,
)
from app.models.teachers import Teacher
from app.services import grading_schemas_service


def _load_schema_graph(db_session, schema_id):
    statement = (
        select(GradingSchema)
        .options(
            selectinload(GradingSchema.grades),
            selectinload(GradingSchema.ranges),
            selectinload(GradingSchema.overrides),
        )
        .where(GradingSchema.id == schema_id)
    )
    return db_session.execute(statement).scalar_one()


def _make_source_schema(db_session, school_id):
    teacher = Teacher(
        school_id=school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    source_schema = GradingSchema(
        school_id=school_id,
        teacher_id=teacher.id,
        name="Source Schema",
        scheme_type=GradingSchemaType.PERCENTAGE,
        max_points=None,
        is_active=True,
        is_template=True,
        is_system=False,
        source_schema_id=None,
    )
    db_session.add(source_schema)
    db_session.commit()
    db_session.refresh(source_schema)

    grade_1 = GradingSchemaGrade(
        grading_schema_id=source_schema.id,
        label="1",
        sort_order=10,
    )
    grade_2 = GradingSchemaGrade(
        grading_schema_id=source_schema.id,
        label="2",
        sort_order=20,
    )
    db_session.add_all([grade_1, grade_2])
    db_session.commit()
    db_session.refresh(grade_1)
    db_session.refresh(grade_2)

    range_1 = GradingSchemaRange(
        grading_schema_id=source_schema.id,
        grade_id=grade_1.id,
        min_value=Decimal("90.00"),
        max_value=Decimal("100.00"),
        min_inclusive=True,
        max_inclusive=True,
    )
    range_2 = GradingSchemaRange(
        grading_schema_id=source_schema.id,
        grade_id=grade_2.id,
        min_value=Decimal("80.00"),
        max_value=Decimal("90.00"),
        min_inclusive=True,
        max_inclusive=False,
    )
    override_1 = GradingSchemaOverride(
        grading_schema_id=source_schema.id,
        grade_id=grade_1.id,
        input_value=Decimal("92.00"),
    )
    db_session.add_all([range_1, range_2, override_1])
    db_session.commit()

    source_schema = _load_schema_graph(db_session, source_schema.id)
    return teacher, source_schema


def test_clone_grading_schema_to_exam_schema(db_session, test_user, seeded_school):
    teacher, source_schema = _make_source_schema(
        db_session=db_session,
        school_id=test_user.school_id,
    )

    result, cloned_schema = grading_schemas_service.clone_grading_schema(
        db=db_session,
        school_id=test_user.school_id,
        source_schema_id=source_schema.id,
        teacher_id=teacher.id,
        name="Exam Working Copy",
        as_template=False,
    )

    assert result == "created"
    assert cloned_schema is not None

    assert cloned_schema.id != source_schema.id
    assert cloned_schema.school_id == source_schema.school_id
    assert cloned_schema.teacher_id == source_schema.teacher_id
    assert cloned_schema.name == "Exam Working Copy"
    assert cloned_schema.scheme_type == source_schema.scheme_type
    assert cloned_schema.max_points == source_schema.max_points

    assert cloned_schema.is_template is False
    assert cloned_schema.is_system is False
    assert cloned_schema.source_schema_id == source_schema.id

    assert len(cloned_schema.grades) == 2
    assert len(cloned_schema.ranges) == 2
    assert len(cloned_schema.overrides) == 1


def test_clone_grading_schema_to_template(db_session, test_user, seeded_school):
    teacher, source_schema = _make_source_schema(
        db_session=db_session,
        school_id=test_user.school_id,
    )

    result, cloned_schema = grading_schemas_service.clone_grading_schema(
        db=db_session,
        school_id=test_user.school_id,
        source_schema_id=source_schema.id,
        teacher_id=teacher.id,
        name="Reusable Copy",
        as_template=True,
    )

    assert result == "created"
    assert cloned_schema is not None

    assert cloned_schema.is_template is True
    assert cloned_schema.is_system is False
    assert cloned_schema.source_schema_id == source_schema.id


def test_clone_grading_schema_copies_grade_labels_and_sort_orders(
    db_session, test_user, seeded_school
):
    teacher, source_schema = _make_source_schema(
        db_session=db_session,
        school_id=test_user.school_id,
    )

    result, cloned_schema = grading_schemas_service.clone_grading_schema(
        db=db_session,
        school_id=test_user.school_id,
        source_schema_id=source_schema.id,
        teacher_id=teacher.id,
        as_template=False,
    )

    assert result == "created"
    assert cloned_schema is not None

    source_grades = sorted(
        [(grade.label, grade.sort_order) for grade in source_schema.grades],
        key=lambda item: item[1],
    )
    cloned_grades = sorted(
        [(grade.label, grade.sort_order) for grade in cloned_schema.grades],
        key=lambda item: item[1],
    )

    assert cloned_grades == source_grades

    source_grade_ids = {grade.id for grade in source_schema.grades}
    cloned_grade_ids = {grade.id for grade in cloned_schema.grades}

    assert source_grade_ids.isdisjoint(cloned_grade_ids)


def test_clone_grading_schema_ranges_and_overrides_reference_cloned_grades(
    db_session, test_user, seeded_school
):
    teacher, source_schema = _make_source_schema(
        db_session=db_session,
        school_id=test_user.school_id,
    )

    result, cloned_schema = grading_schemas_service.clone_grading_schema(
        db=db_session,
        school_id=test_user.school_id,
        source_schema_id=source_schema.id,
        teacher_id=teacher.id,
        as_template=False,
    )

    assert result == "created"
    assert cloned_schema is not None

    source_grade_ids = {grade.id for grade in source_schema.grades}
    cloned_grade_ids = {grade.id for grade in cloned_schema.grades}

    assert len(cloned_grade_ids) == 2

    for range_rule in cloned_schema.ranges:
        assert range_rule.grade_id in cloned_grade_ids
        assert range_rule.grade_id not in source_grade_ids

    for override_rule in cloned_schema.overrides:
        assert override_rule.grade_id in cloned_grade_ids
        assert override_rule.grade_id not in source_grade_ids


def test_clone_grading_schema_preserves_range_and_override_values(
    db_session, test_user, seeded_school
):
    teacher, source_schema = _make_source_schema(
        db_session=db_session,
        school_id=test_user.school_id,
    )

    result, cloned_schema = grading_schemas_service.clone_grading_schema(
        db=db_session,
        school_id=test_user.school_id,
        source_schema_id=source_schema.id,
        teacher_id=teacher.id,
        as_template=False,
    )

    assert result == "created"
    assert cloned_schema is not None

    source_grade_by_id = {grade.id: grade for grade in source_schema.grades}
    cloned_grade_by_id = {grade.id: grade for grade in cloned_schema.grades}

    source_ranges = sorted(
        [
            (
                source_grade_by_id[item.grade_id].label,
                item.min_value,
                item.max_value,
                item.min_inclusive,
                item.max_inclusive,
            )
            for item in source_schema.ranges
        ],
        key=lambda item: (item[1], item[2], item[0]),
    )
    cloned_ranges = sorted(
        [
            (
                cloned_grade_by_id[item.grade_id].label,
                item.min_value,
                item.max_value,
                item.min_inclusive,
                item.max_inclusive,
            )
            for item in cloned_schema.ranges
        ],
        key=lambda item: (item[1], item[2], item[0]),
    )

    assert cloned_ranges == source_ranges

    source_overrides = sorted(
        [
            (
                source_grade_by_id[item.grade_id].label,
                item.input_value,
            )
            for item in source_schema.overrides
        ],
        key=lambda item: (item[1], item[0]),
    )
    cloned_overrides = sorted(
        [
            (
                cloned_grade_by_id[item.grade_id].label,
                item.input_value,
            )
            for item in cloned_schema.overrides
        ],
        key=lambda item: (item[1], item[0]),
    )

    assert cloned_overrides == source_overrides


def test_clone_grading_schema_with_unknown_source_returns_not_found(
    db_session, test_user, seeded_school
):
    teacher = Teacher(
        school_id=test_user.school_id,
        name="Teacher One",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)

    result, cloned_schema = grading_schemas_service.clone_grading_schema(
        db=db_session,
        school_id=test_user.school_id,
        source_schema_id=UUID("00000000-0000-0000-0000-000000000999"),
        teacher_id=teacher.id,
        as_template=False,
    )

    assert result == "source_schema_not_found"
    assert cloned_schema is None
