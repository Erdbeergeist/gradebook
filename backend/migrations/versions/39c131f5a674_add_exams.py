"""add exams

Revision ID: 39c131f5a674
Revises: bfc7f85ce783
Create Date: 2026-04-05 11:01:05.538973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "39c131f5a674"
down_revision: Union[str, Sequence[str], None] = "bfc7f85ce783"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


exam_type_enum = postgresql.ENUM(
    "written",
    "oral",
    "practical",
    "presentation",
    "other",
    name="exam_type_enum",
    create_type=False,
)

exam_type_detail_enum = postgresql.ENUM(
    "essay",
    "multiple_choice",
    "short_answer",
    "individual_oral",
    "group_oral",
    "lab",
    "project",
    "slides",
    "other",
    name="exam_type_detail_enum",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    exam_type_enum.create(bind, checkfirst=True)
    exam_type_detail_enum.create(bind, checkfirst=True)

    op.create_table(
        "exams",
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("exam_type", exam_type_enum, nullable=False),
        sa.Column("exam_type_detail", exam_type_detail_enum, nullable=True),
        sa.Column("max_points", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("weight", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exams_class_id"), "exams", ["class_id"], unique=False)
    op.create_index(op.f("ix_exams_school_id"), "exams", ["school_id"], unique=False)

    op.create_foreign_key(
        "exam_results_exam_id_fkey",
        "exam_results",
        "exams",
        ["exam_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("exam_results_exam_id_fkey", "exam_results", type_="foreignkey")
    op.drop_index(op.f("ix_exams_school_id"), table_name="exams")
    op.drop_index(op.f("ix_exams_class_id"), table_name="exams")
    op.drop_table("exams")

    bind = op.get_bind()
    exam_type_detail_enum.drop(bind, checkfirst=True)
    exam_type_enum.drop(bind, checkfirst=True)
