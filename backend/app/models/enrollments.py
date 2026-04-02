from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, mapped_column

from .base import Base, UUIDMixin, TimestampMixin


class Enrollment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "enrollments"

    class_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    student_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("class_id", "student_id", name="uq_class_student"),
    )

    class_ = relationship("Class", back_populates="enrollments")
    student = relationship("Student", back_populates="enrollments")
