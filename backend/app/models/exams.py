from decimal import Decimal
from enum import Enum

from sqlalchemy import ForeignKey, Numeric, String, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, mapped_column

from .base import Base, UUIDMixin, TimestampMixin


class ExamType(str, Enum):
    WRITTEN = "written"
    ORAL = "oral"
    PRACTICAL = "practical"
    PRESENTATION = "presentation"
    OTHER = "other"


class ExamTypeDetail(str, Enum):
    ESSAY = "essay"
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    INDIVIDUAL_ORAL = "individual_oral"
    GROUP_ORAL = "group_oral"
    LAB = "lab"
    PROJECT = "project"
    SLIDES = "slides"
    OTHER = "other"


class Exam(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "exams"

    school_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True
    )
    class_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False, index=True
    )
    grading_schema_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grading_schemas.id"),
        nullable=False,
        index=True,
    )
    name = mapped_column(String, nullable=False)
    exam_type = mapped_column(
        SqlEnum(
            ExamType,
            name="exam_type_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    exam_type_detail = mapped_column(
        SqlEnum(
            ExamTypeDetail,
            name="exam_type_detail_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=True,
    )
    max_points = mapped_column(Numeric(10, 2), nullable=False)
    weight = mapped_column(Numeric(10, 2), nullable=False, default=1.00)

    school = relationship("School")
    class_ = relationship("Class", back_populates="exams")
    grading_schema = relationship("GradingSchema", back_populates="exams")
    results = relationship(
        "ExamResult", back_populates="exam", cascade="all, delete-orphan"
    )
