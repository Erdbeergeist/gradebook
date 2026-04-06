"""add grading_schemas

Revision ID: 2699656ca9ad
Revises: c75f6666ef71
Create Date: 2026-04-06 15:10:49.729628

"""
from typing import Sequence, Union
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "2699656ca9ad"
down_revision: Union[str, Sequence[str], None] = "c75f6666ef71"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


grading_schema_type_enum = sa.Enum(
    "percentage",
    "points",
    name="grading_schema_type_enum",
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    grading_schema_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "grade_catalogs",
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_grade_catalogs_code"), "grade_catalogs", ["code"], unique=True
    )

    op.create_table(
        "grade_catalog_items",
        sa.Column("grade_catalog_id", sa.UUID(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["grade_catalog_id"], ["grade_catalogs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "grade_catalog_id", "label", name="uq_grade_catalog_item_label"
        ),
        sa.UniqueConstraint(
            "grade_catalog_id", "sort_order", name="uq_grade_catalog_item_sort_order"
        ),
    )
    op.create_index(
        op.f("ix_grade_catalog_items_grade_catalog_id"),
        "grade_catalog_items",
        ["grade_catalog_id"],
        unique=False,
    )

    op.create_table(
        "grading_schemas",
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("teacher_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("scheme_type", grading_schema_type_enum, nullable=False),
        sa.Column("max_points", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_grading_schemas_school_id"),
        "grading_schemas",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_grading_schemas_teacher_id"),
        "grading_schemas",
        ["teacher_id"],
        unique=False,
    )

    op.create_table(
        "grading_schema_grades",
        sa.Column("grading_schema_id", sa.UUID(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["grading_schema_id"], ["grading_schemas.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "grading_schema_id", "label", name="uq_grading_schema_grade_label"
        ),
        sa.UniqueConstraint(
            "grading_schema_id", "sort_order", name="uq_grading_schema_grade_sort_order"
        ),
    )
    op.create_index(
        op.f("ix_grading_schema_grades_grading_schema_id"),
        "grading_schema_grades",
        ["grading_schema_id"],
        unique=False,
    )

    op.create_table(
        "grading_schema_overrides",
        sa.Column("grading_schema_id", sa.UUID(), nullable=False),
        sa.Column("grade_id", sa.UUID(), nullable=False),
        sa.Column("input_value", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["grade_id"], ["grading_schema_grades.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["grading_schema_id"], ["grading_schemas.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "grading_schema_id",
            "input_value",
            name="uq_grading_schema_override_input_value",
        ),
    )
    op.create_index(
        op.f("ix_grading_schema_overrides_grade_id"),
        "grading_schema_overrides",
        ["grade_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_grading_schema_overrides_grading_schema_id"),
        "grading_schema_overrides",
        ["grading_schema_id"],
        unique=False,
    )

    op.create_table(
        "grading_schema_ranges",
        sa.Column("grading_schema_id", sa.UUID(), nullable=False),
        sa.Column("grade_id", sa.UUID(), nullable=False),
        sa.Column("min_value", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("max_value", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("min_inclusive", sa.Boolean(), nullable=False),
        sa.Column("max_inclusive", sa.Boolean(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["grade_id"], ["grading_schema_grades.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["grading_schema_id"], ["grading_schemas.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_grading_schema_ranges_grade_id"),
        "grading_schema_ranges",
        ["grade_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_grading_schema_ranges_grading_schema_id"),
        "grading_schema_ranges",
        ["grading_schema_id"],
        unique=False,
    )

    now = datetime.now(timezone.utc)

    de_standard_id = uuid.uuid4()
    de_oberstufe_id = uuid.uuid4()

    grade_catalogs = sa.table(
        "grade_catalogs",
        sa.column("id", sa.UUID()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    grade_catalog_items = sa.table(
        "grade_catalog_items",
        sa.column("id", sa.UUID()),
        sa.column("grade_catalog_id", sa.UUID()),
        sa.column("label", sa.String()),
        sa.column("sort_order", sa.Integer()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    op.bulk_insert(
        grade_catalogs,
        [
            {
                "id": de_standard_id,
                "code": "de_standard",
                "name": "German standard grades",
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": de_oberstufe_id,
                "code": "de_oberstufe",
                "name": "German upper secondary points",
                "created_at": now,
                "updated_at": now,
            },
        ],
    )

    de_standard_labels = [
        "1",
        "1-",
        "2+",
        "2",
        "2-",
        "3+",
        "3",
        "3-",
        "4+",
        "4",
        "4-",
        "5+",
        "5",
        "5-",
        "6",
    ]
    de_oberstufe_labels = [
        "15",
        "14",
        "13",
        "12",
        "11",
        "10",
        "9",
        "8",
        "7",
        "6",
        "5",
        "4",
        "3",
        "2",
        "1",
        "0",
    ]

    catalog_item_rows = []
    for index, label in enumerate(de_standard_labels, start=1):
        catalog_item_rows.append(
            {
                "id": uuid.uuid4(),
                "grade_catalog_id": de_standard_id,
                "label": label,
                "sort_order": index * 10,
                "created_at": now,
                "updated_at": now,
            }
        )

    for index, label in enumerate(de_oberstufe_labels, start=1):
        catalog_item_rows.append(
            {
                "id": uuid.uuid4(),
                "grade_catalog_id": de_oberstufe_id,
                "label": label,
                "sort_order": index * 10,
                "created_at": now,
                "updated_at": now,
            }
        )

    op.bulk_insert(grade_catalog_items, catalog_item_rows)

    op.add_column("exams", sa.Column("grading_schema_id", sa.UUID(), nullable=True))
    op.create_index(
        op.f("ix_exams_grading_schema_id"), "exams", ["grading_schema_id"], unique=False
    )

    # Backfill existing exams:
    # create one migrated default percentage schema per teacher who already has exams,
    # then assign all that teacher's exams to it.
    connection = bind

    teacher_exam_rows = connection.execute(
        sa.text(
            """
            SELECT DISTINCT c.teacher_id, c.school_id
            FROM exams e
            JOIN classes c ON c.id = e.class_id
            """
        )
    ).fetchall()

    for teacher_id, school_id in teacher_exam_rows:
        schema_id = uuid.uuid4()
        connection.execute(
            sa.text(
                """
                INSERT INTO grading_schemas
                    (id, school_id, teacher_id, name, scheme_type, max_points, is_active, created_at, updated_at)
                VALUES
                    (:id, :school_id, :teacher_id, :name, :scheme_type, :max_points, :is_active, :created_at, :updated_at)
                """
            ),
            {
                "id": schema_id,
                "school_id": school_id,
                "teacher_id": teacher_id,
                "name": "Migrated default percentage schema",
                "scheme_type": "percentage",
                "max_points": None,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
        )

        for index, label in enumerate(de_standard_labels, start=1):
            connection.execute(
                sa.text(
                    """
                    INSERT INTO grading_schema_grades
                        (id, grading_schema_id, label, sort_order, created_at, updated_at)
                    VALUES
                        (:id, :grading_schema_id, :label, :sort_order, :created_at, :updated_at)
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "grading_schema_id": schema_id,
                    "label": label,
                    "sort_order": index * 10,
                    "created_at": now,
                    "updated_at": now,
                },
            )

        connection.execute(
            sa.text(
                """
                UPDATE exams e
                SET grading_schema_id = :schema_id
                FROM classes c
                WHERE c.id = e.class_id
                  AND c.teacher_id = :teacher_id
                  AND e.grading_schema_id IS NULL
                """
            ),
            {
                "schema_id": schema_id,
                "teacher_id": teacher_id,
            },
        )

    op.create_foreign_key(
        "exams_grading_schema_id_fkey",
        "exams",
        "grading_schemas",
        ["grading_schema_id"],
        ["id"],
    )
    op.alter_column("exams", "grading_schema_id", nullable=False)

    op.drop_table("grading_schemes")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        "grading_schemes",
        sa.Column("class_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("grade", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column(
            "min_percentage",
            sa.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["class_id"], ["classes.id"], name=op.f("grading_schemes_class_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("grading_schemes_pkey")),
    )

    op.drop_constraint("exams_grading_schema_id_fkey", "exams", type_="foreignkey")
    op.drop_index(op.f("ix_exams_grading_schema_id"), table_name="exams")
    op.drop_column("exams", "grading_schema_id")

    op.drop_index(
        op.f("ix_grading_schema_ranges_grading_schema_id"),
        table_name="grading_schema_ranges",
    )
    op.drop_index(
        op.f("ix_grading_schema_ranges_grade_id"), table_name="grading_schema_ranges"
    )
    op.drop_table("grading_schema_ranges")

    op.drop_index(
        op.f("ix_grading_schema_overrides_grading_schema_id"),
        table_name="grading_schema_overrides",
    )
    op.drop_index(
        op.f("ix_grading_schema_overrides_grade_id"),
        table_name="grading_schema_overrides",
    )
    op.drop_table("grading_schema_overrides")

    op.drop_index(
        op.f("ix_grading_schema_grades_grading_schema_id"),
        table_name="grading_schema_grades",
    )
    op.drop_table("grading_schema_grades")

    op.drop_index(op.f("ix_grading_schemas_teacher_id"), table_name="grading_schemas")
    op.drop_index(op.f("ix_grading_schemas_school_id"), table_name="grading_schemas")
    op.drop_table("grading_schemas")

    op.drop_index(
        op.f("ix_grade_catalog_items_grade_catalog_id"),
        table_name="grade_catalog_items",
    )
    op.drop_table("grade_catalog_items")

    op.drop_index(op.f("ix_grade_catalogs_code"), table_name="grade_catalogs")
    op.drop_table("grade_catalogs")

    bind = op.get_bind()
    grading_schema_type_enum.drop(bind, checkfirst=True)
