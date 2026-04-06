from __future__ import annotations

import enum

from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ExamResultStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    EXCUSED = "excused"
    MISSING = "missing"


class ExamResult(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "exam_results"
    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", name="uq_exam_result_exam_student"),
    )

    exam_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    points = mapped_column(Numeric(10, 2), nullable=True)
    comment = mapped_column(String, nullable=True)
    status = mapped_column(
        SqlEnum(
            ExamResultStatus,
            name="exam_result_status_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=True,
    )
    graded_at = mapped_column(DateTime(timezone=True), nullable=True)

    exam = relationship("Exam", back_populates="results")
    student = relationship("Student")
