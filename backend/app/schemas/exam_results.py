from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.exam_results import ExamResultStatus


class ExamResultCreate(BaseModel):
    exam_id: UUID
    student_id: UUID
    points: Decimal | None = Field(default=None, ge=0)
    comment: str | None = Field(default=None, max_length=2000)
    status: ExamResultStatus | None = None
    graded_at: datetime | None = None

    @model_validator(mode="after")
    def validate_points_for_status(self) -> "ExamResultCreate":
        if self.status == ExamResultStatus.PRESENT and self.points is None:
            raise ValueError("points are required when status is 'present'.")

        if (
            self.status
            in {
                ExamResultStatus.ABSENT,
                ExamResultStatus.EXCUSED,
                ExamResultStatus.MISSING,
            }
            and self.points is not None
        ):
            raise ValueError(
                "points must be omitted when status is absent, excused, or missing."
            )

        return self


class ExamResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exam_id: UUID
    student_id: UUID
    points: Decimal | None
    comment: str | None
    status: ExamResultStatus | None
    graded_at: datetime | None
    resolved_input_value: Decimal | None
    resolved_grade_label: str | None
    created_at: datetime
    updated_at: datetime
