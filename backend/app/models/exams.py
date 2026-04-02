from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, mapped_column

from .base import Base, UUIDMixin, TimestampMixin


class Exam(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "exams"

    class_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )

    name = mapped_column(String, nullable=False)
    max_points = mapped_column(Float, nullable=False)
    weight = mapped_column(Float, nullable=False, default=1.0)

    class_ = relationship("Class", back_populates="exams")
    results = relationship("ExamResult", back_populates="exam")
