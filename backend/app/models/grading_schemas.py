from __future__ import annotations

import enum

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Enum as SqlEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class GradingSchemaType(str, enum.Enum):
    PERCENTAGE = "percentage"
    POINTS = "points"


class GradingSchema(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "grading_schemas"

    school_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id"),
        nullable=False,
        index=True,
    )
    teacher_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id"),
        nullable=False,
        index=True,
    )
    name = mapped_column(String, nullable=False)
    scheme_type = mapped_column(
        SqlEnum(
            GradingSchemaType,
            name="grading_schema_type_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    max_points = mapped_column(Numeric(10, 2), nullable=True)

    is_active = mapped_column(Boolean, nullable=False, default=True)

    is_template = mapped_column(Boolean, nullable=False, default=True)
    is_system = mapped_column(Boolean, nullable=False, default=False)

    source_schema_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grading_schemas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    school = relationship("School")
    teacher = relationship("Teacher", back_populates="grading_schemas")

    source_schema = relationship(
        "GradingSchema",
        remote_side="GradingSchema.id",
        back_populates="derived_schemas",
    )
    derived_schemas = relationship(
        "GradingSchema",
        back_populates="source_schema",
    )

    grades = relationship(
        "GradingSchemaGrade",
        back_populates="grading_schema",
        cascade="all, delete-orphan",
        order_by="GradingSchemaGrade.sort_order.asc()",
    )
    ranges = relationship(
        "GradingSchemaRange",
        back_populates="grading_schema",
        cascade="all, delete-orphan",
    )
    overrides = relationship(
        "GradingSchemaOverride",
        back_populates="grading_schema",
        cascade="all, delete-orphan",
    )
    exams = relationship("Exam", back_populates="grading_schema")


class GradingSchemaGrade(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "grading_schema_grades"
    __table_args__ = (
        UniqueConstraint(
            "grading_schema_id",
            "label",
            name="uq_grading_schema_grade_label",
        ),
        UniqueConstraint(
            "grading_schema_id",
            "sort_order",
            name="uq_grading_schema_grade_sort_order",
        ),
    )

    grading_schema_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grading_schemas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label = mapped_column(String, nullable=False)
    sort_order = mapped_column(Integer, nullable=False)

    grading_schema = relationship("GradingSchema", back_populates="grades")
    ranges = relationship("GradingSchemaRange", back_populates="grade")
    overrides = relationship("GradingSchemaOverride", back_populates="grade")


class GradingSchemaRange(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "grading_schema_ranges"

    grading_schema_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grading_schemas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grade_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grading_schema_grades.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    min_value = mapped_column(Numeric(10, 2), nullable=False)
    max_value = mapped_column(Numeric(10, 2), nullable=False)
    min_inclusive = mapped_column(Boolean, nullable=False)
    max_inclusive = mapped_column(Boolean, nullable=False)

    grading_schema = relationship("GradingSchema", back_populates="ranges")
    grade = relationship("GradingSchemaGrade", back_populates="ranges")


class GradingSchemaOverride(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "grading_schema_overrides"
    __table_args__ = (
        UniqueConstraint(
            "grading_schema_id",
            "input_value",
            name="uq_grading_schema_override_input_value",
        ),
    )

    grading_schema_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grading_schemas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grade_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grading_schema_grades.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    input_value = mapped_column(Numeric(10, 2), nullable=False)

    grading_schema = relationship("GradingSchema", back_populates="overrides")
    grade = relationship("GradingSchemaGrade", back_populates="overrides")
