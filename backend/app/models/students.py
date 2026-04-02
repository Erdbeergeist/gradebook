from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, mapped_column

from .base import Base, UUIDMixin, TimestampMixin


class Student(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "students"

    school_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )

    first_name = mapped_column(String, nullable=False)
    last_name = mapped_column(String, nullable=False)

    school = relationship("School", back_populates="students")
    enrollments = relationship("Enrollment", back_populates="student")
