from sqlalchemy import String
from sqlalchemy.orm import relationship, mapped_column

from .base import Base, UUIDMixin, TimestampMixin


class School(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "schools"

    name = mapped_column(String, nullable=False)

    teachers = relationship("Teacher", back_populates="school")
    students = relationship("Student", back_populates="school")
    classes = relationship("Class", back_populates="school")
