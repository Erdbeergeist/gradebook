from app.models.grading_schemas import GradingSchema, GradingSchemaType
from app.services.grading_schemas_service import (
    can_clone_schema,
    can_delete_schema,
    can_edit_schema,
    can_promote_schema_to_template,
    can_replace_template,
    is_exam_schema,
    is_system_schema,
    is_template_schema,
)
from uuid import UUID


def make_schema(
    *,
    is_template: bool,
    is_system: bool,
):
    return GradingSchema(
        school_id=UUID("00000000-0000-0000-0000-000000000100"),
        teacher_id=UUID("00000000-0000-0000-0000-000000000200"),
        name="Schema",
        scheme_type=GradingSchemaType.PERCENTAGE,
        max_points=None,
        is_active=True,
        is_template=is_template,
        is_system=is_system,
    )


def test_system_template_schema_policies():
    schema = make_schema(is_template=True, is_system=True)

    assert is_system_schema(schema) is True
    assert is_template_schema(schema) is True
    assert is_exam_schema(schema) is False
    assert can_edit_schema(schema) is False
    assert can_delete_schema(schema) is False
    assert can_clone_schema(schema) is True
    assert can_promote_schema_to_template(schema) is False


def test_user_template_schema_policies():
    schema = make_schema(is_template=True, is_system=False)

    assert is_system_schema(schema) is False
    assert is_template_schema(schema) is True
    assert is_exam_schema(schema) is False
    assert can_edit_schema(schema) is True
    assert can_delete_schema(schema) is True
    assert can_clone_schema(schema) is True
    assert can_promote_schema_to_template(schema) is False


def test_exam_schema_policies():
    schema = make_schema(is_template=False, is_system=False)

    assert is_system_schema(schema) is False
    assert is_template_schema(schema) is False
    assert is_exam_schema(schema) is True
    assert can_edit_schema(schema) is True
    assert can_delete_schema(schema) is False
    assert can_clone_schema(schema) is True
    assert can_promote_schema_to_template(schema) is True


def test_can_replace_template_allows_user_template_target_and_non_system_source():
    target_schema = make_schema(is_template=True, is_system=False)
    source_schema = make_schema(is_template=False, is_system=False)

    assert can_replace_template(target_schema, source_schema) is True


def test_can_replace_template_rejects_system_target():
    target_schema = make_schema(is_template=True, is_system=True)
    source_schema = make_schema(is_template=False, is_system=False)

    assert can_replace_template(target_schema, source_schema) is False
