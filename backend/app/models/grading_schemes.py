from sqlalchemy import Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, mapped_column

from .base import Base, UUIDMixin, TimestampMixin


class GradingScheme(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "grading_schemes"

    class_id = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )

    grade = mapped_column(Integer, nullable=False)
    min_percentage = mapped_column(Float, nullable=False)

    class_ = relationship("Class", back_populates="grading_schemes")
