"""extensions for grading_schemas

Revision ID: 0410a72f5ce0
Revises: 54c078bec995
Create Date: 2026-04-07 20:25:36.766666

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0410a72f5ce0"
down_revision: Union[str, Sequence[str], None] = "54c078bec995"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "grading_schemas",
        sa.Column(
            "is_template",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "grading_schemas",
        sa.Column(
            "is_system",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "grading_schemas",
        sa.Column("source_schema_id", sa.UUID(), nullable=True),
    )

    op.create_index(
        op.f("ix_grading_schemas_source_schema_id"),
        "grading_schemas",
        ["source_schema_id"],
        unique=False,
    )
    op.create_foreign_key(
        "grading_schemas_source_schema_id_fkey",
        "grading_schemas",
        "grading_schemas",
        ["source_schema_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.alter_column("grading_schemas", "is_template", server_default=None)
    op.alter_column("grading_schemas", "is_system", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "grading_schemas_source_schema_id_fkey",
        "grading_schemas",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_grading_schemas_source_schema_id"),
        table_name="grading_schemas",
    )
    op.drop_column("grading_schemas", "source_schema_id")
    op.drop_column("grading_schemas", "is_system")
    op.drop_column("grading_schemas", "is_template")
