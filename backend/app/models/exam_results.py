from sqlalchemy import ForeignKey, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, mapped_column

from .base import Base, UUIDMixin, TimestampMixin


class ExamResult(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "exam_results"

    exam_id = mapped_column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    student_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )

    points = mapped_column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", name="uq_exam_student"),
    )

    exam = relationship("Exam", back_populates="results")
    student = relationship("Student")
