"""update

Revision ID: c75f6666ef71
Revises: 39c131f5a674
Create Date: 2026-04-06 11:16:38.135086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c75f6666ef71"
down_revision: Union[str, Sequence[str], None] = "39c131f5a674"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


exam_result_status_enum = sa.Enum(
    "present",
    "absent",
    "excused",
    "missing",
    name="exam_result_status_enum",
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    exam_result_status_enum.create(bind, checkfirst=True)

    op.add_column("exam_results", sa.Column("comment", sa.String(), nullable=True))
    op.add_column(
        "exam_results",
        sa.Column("status", exam_result_status_enum, nullable=True),
    )
    op.add_column(
        "exam_results",
        sa.Column("graded_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.alter_column(
        "exam_results",
        "points",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        type_=sa.Numeric(precision=10, scale=2),
        nullable=True,
    )

    op.drop_constraint("uq_exam_student", "exam_results", type_="unique")

    op.create_index(
        op.f("ix_exam_results_exam_id"),
        "exam_results",
        ["exam_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_exam_results_student_id"),
        "exam_results",
        ["student_id"],
        unique=False,
    )

    op.create_unique_constraint(
        "uq_exam_result_exam_student",
        "exam_results",
        ["exam_id", "student_id"],
    )

    op.drop_constraint("exam_results_exam_id_fkey", "exam_results", type_="foreignkey")
    op.drop_constraint(
        "exam_results_student_id_fkey", "exam_results", type_="foreignkey"
    )

    op.create_foreign_key(
        "exam_results_exam_id_fkey",
        "exam_results",
        "exams",
        ["exam_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "exam_results_student_id_fkey",
        "exam_results",
        "students",
        ["student_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "exam_results_student_id_fkey", "exam_results", type_="foreignkey"
    )
    op.drop_constraint("exam_results_exam_id_fkey", "exam_results", type_="foreignkey")

    op.create_foreign_key(
        "exam_results_student_id_fkey",
        "exam_results",
        "students",
        ["student_id"],
        ["id"],
    )
    op.create_foreign_key(
        "exam_results_exam_id_fkey",
        "exam_results",
        "exams",
        ["exam_id"],
        ["id"],
    )

    op.drop_constraint(
        "uq_exam_result_exam_student",
        "exam_results",
        type_="unique",
    )

    op.drop_index(op.f("ix_exam_results_student_id"), table_name="exam_results")
    op.drop_index(op.f("ix_exam_results_exam_id"), table_name="exam_results")

    op.create_unique_constraint(
        "uq_exam_student",
        "exam_results",
        ["exam_id", "student_id"],
        postgresql_nulls_not_distinct=False,
    )

    op.alter_column(
        "exam_results",
        "points",
        existing_type=sa.Numeric(precision=10, scale=2),
        type_=sa.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )

    op.drop_column("exam_results", "graded_at")
    op.drop_column("exam_results", "status")
    op.drop_column("exam_results", "comment")

    bind = op.get_bind()
    exam_result_status_enum.drop(bind, checkfirst=True)
