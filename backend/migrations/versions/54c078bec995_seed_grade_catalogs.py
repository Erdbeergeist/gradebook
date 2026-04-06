"""seed grade catalogs

Revision ID: 54c078bec995
Revises: 2699656ca9ad
Create Date: 2026-04-06 15:43:18.154818

"""
from typing import Sequence, Union
import uuid
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "54c078bec995"
down_revision: Union[str, Sequence[str], None] = "2699656ca9ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    now = datetime.now(timezone.utc)

    existing_codes = {
        row[0]
        for row in connection.execute(
            sa.text("SELECT code FROM grade_catalogs")
        ).fetchall()
    }

    de_standard_id = uuid.uuid4()
    de_oberstufe_id = uuid.uuid4()

    if "de_standard" not in existing_codes:
        connection.execute(
            sa.text(
                """
                INSERT INTO grade_catalogs (id, code, name, created_at, updated_at)
                VALUES (:id, :code, :name, :created_at, :updated_at)
                """
            ),
            {
                "id": de_standard_id,
                "code": "de_standard",
                "name": "German standard grades",
                "created_at": now,
                "updated_at": now,
            },
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

        for index, label in enumerate(de_standard_labels, start=1):
            connection.execute(
                sa.text(
                    """
                    INSERT INTO grade_catalog_items
                        (id, grade_catalog_id, label, sort_order, created_at, updated_at)
                    VALUES
                        (:id, :grade_catalog_id, :label, :sort_order, :created_at, :updated_at)
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "grade_catalog_id": de_standard_id,
                    "label": label,
                    "sort_order": index * 10,
                    "created_at": now,
                    "updated_at": now,
                },
            )

    if "de_oberstufe" not in existing_codes:
        connection.execute(
            sa.text(
                """
                INSERT INTO grade_catalogs (id, code, name, created_at, updated_at)
                VALUES (:id, :code, :name, :created_at, :updated_at)
                """
            ),
            {
                "id": de_oberstufe_id,
                "code": "de_oberstufe",
                "name": "German upper secondary points",
                "created_at": now,
                "updated_at": now,
            },
        )

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

        for index, label in enumerate(de_oberstufe_labels, start=1):
            connection.execute(
                sa.text(
                    """
                    INSERT INTO grade_catalog_items
                        (id, grade_catalog_id, label, sort_order, created_at, updated_at)
                    VALUES
                        (:id, :grade_catalog_id, :label, :sort_order, :created_at, :updated_at)
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "grade_catalog_id": de_oberstufe_id,
                    "label": label,
                    "sort_order": index * 10,
                    "created_at": now,
                    "updated_at": now,
                },
            )


def downgrade() -> None:
    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            DELETE FROM grade_catalog_items
            WHERE grade_catalog_id IN (
                SELECT id
                FROM grade_catalogs
                WHERE code IN ('de_standard', 'de_oberstufe')
            )
            """
        )
    )

    connection.execute(
        sa.text(
            """
            DELETE FROM grade_catalogs
            WHERE code IN ('de_standard', 'de_oberstufe')
            """
        )
    )
