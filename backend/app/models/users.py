from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    school_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id"),
        nullable=False,
        index=True,
    )
    email = mapped_column(String, nullable=False, unique=True, index=True)
    password_hash = mapped_column(String, nullable=False)
    role = mapped_column(String, nullable=False, default="teacher")
    is_active = mapped_column(Boolean, nullable=False, default=True)

    school = relationship("School")
    teacher = relationship("Teacher", back_populates="user", uselist=False)
