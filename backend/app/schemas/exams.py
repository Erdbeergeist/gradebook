from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.exams import ExamType, ExamTypeDetail


_ALLOWED_DETAILS_BY_TYPE = {
    ExamType.WRITTEN: {
        ExamTypeDetail.ESSAY,
        ExamTypeDetail.MULTIPLE_CHOICE,
        ExamTypeDetail.SHORT_ANSWER,
        ExamTypeDetail.OTHER,
    },
    ExamType.ORAL: {
        ExamTypeDetail.INDIVIDUAL_ORAL,
        ExamTypeDetail.GROUP_ORAL,
        ExamTypeDetail.OTHER,
    },
    ExamType.PRACTICAL: {
        ExamTypeDetail.LAB,
        ExamTypeDetail.PROJECT,
        ExamTypeDetail.OTHER,
    },
    ExamType.PRESENTATION: {
        ExamTypeDetail.SLIDES,
        ExamTypeDetail.PROJECT,
        ExamTypeDetail.OTHER,
    },
    ExamType.OTHER: {
        ExamTypeDetail.OTHER,
    },
}


class ExamCreate(BaseModel):
    class_id: UUID
    name: str = Field(min_length=1, max_length=255)
    exam_type: ExamType
    grading_schema_id: UUID
    exam_type_detail: ExamTypeDetail | None = None
    max_points: Decimal = Field(gt=0)
    weight: Decimal = Field(default=Decimal("1.00"), gt=0)

    @model_validator(mode="after")
    def validate_exam_type_detail(self):
        if self.exam_type_detail is None:
            return self

        allowed_details = _ALLOWED_DETAILS_BY_TYPE[self.exam_type]
        if self.exam_type_detail not in allowed_details:
            raise ValueError(
                "exam_type_detail is not valid for the selected exam_type."
            )
        return self


class ExamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    class_id: UUID
    name: str
    exam_type: ExamType
    exam_type_detail: ExamTypeDetail | None
    max_points: Decimal
    weight: Decimal
    grading_schema_id: UUID
    created_at: datetime
    updated_at: datetime
