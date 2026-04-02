from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, mapped_column

from .base import Base, UUIDMixin, TimestampMixin


class Teacher(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "teachers"

    school_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )

    name = mapped_column(String, nullable=False)

    school = relationship("School", back_populates="teachers")
    classes = relationship("Class", back_populates="teacher")
