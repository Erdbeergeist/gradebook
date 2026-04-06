from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class GradeCatalog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "grade_catalogs"

    code = mapped_column(String, nullable=False, unique=True, index=True)
    name = mapped_column(String, nullable=False)

    items = relationship(
        "GradeCatalogItem",
        back_populates="grade_catalog",
        cascade="all, delete-orphan",
        order_by="GradeCatalogItem.sort_order.asc()",
    )


class GradeCatalogItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "grade_catalog_items"
    __table_args__ = (
        UniqueConstraint(
            "grade_catalog_id", "label", name="uq_grade_catalog_item_label"
        ),
        UniqueConstraint(
            "grade_catalog_id",
            "sort_order",
            name="uq_grade_catalog_item_sort_order",
        ),
    )

    grade_catalog_id = mapped_column(
        ForeignKey("grade_catalogs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label = mapped_column(String, nullable=False)
    sort_order = mapped_column(Integer, nullable=False)

    grade_catalog = relationship("GradeCatalog", back_populates="items")
