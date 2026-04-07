from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.grading_schemas import GradingSchemaType


class GradeCatalogItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    label: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class GradeCatalogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    items: list[GradeCatalogItemRead]
    created_at: datetime
    updated_at: datetime


class GradingSchemaGradeInput(BaseModel):
    label: str = Field(min_length=1, max_length=50)
    sort_order: int


class GradingSchemaRangeInput(BaseModel):
    grade_label: str = Field(min_length=1, max_length=50)
    min_value: Decimal
    max_value: Decimal
    min_inclusive: bool = True
    max_inclusive: bool = False

    @model_validator(mode="after")
    def validate_bounds(self) -> "GradingSchemaRangeInput":
        if self.min_value > self.max_value:
            raise ValueError("min_value must be less than or equal to max_value.")
        return self


class GradingSchemaOverrideInput(BaseModel):
    input_value: Decimal
    grade_label: str = Field(min_length=1, max_length=50)


class GradingSchemaCreate(BaseModel):
    teacher_id: UUID
    name: str = Field(min_length=1, max_length=255)
    scheme_type: GradingSchemaType
    max_points: Decimal | None = None
    grade_catalog_code: str | None = None
    grades: list[GradingSchemaGradeInput] = Field(default_factory=list)
    ranges: list[GradingSchemaRangeInput] = Field(default_factory=list)
    overrides: list[GradingSchemaOverrideInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_scheme_shape(self) -> "GradingSchemaCreate":
        if (
            self.scheme_type == GradingSchemaType.PERCENTAGE
            and self.max_points is not None
        ):
            raise ValueError("max_points must be null for percentage grading schemas.")

        if self.scheme_type == GradingSchemaType.POINTS:
            if self.max_points is None or self.max_points <= 0:
                raise ValueError(
                    "max_points must be provided and > 0 for points grading schemas."
                )

        if self.grade_catalog_code is None and len(self.grades) == 0:
            raise ValueError("Provide either grade_catalog_code or grades.")

        return self


class GradingSchemaUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    scheme_type: GradingSchemaType
    max_points: Decimal | None = None
    grade_catalog_code: str | None = None
    grades: list[GradingSchemaGradeInput] = Field(default_factory=list)
    ranges: list[GradingSchemaRangeInput] = Field(default_factory=list)
    overrides: list[GradingSchemaOverrideInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_scheme_shape(self) -> "GradingSchemaUpdate":
        if (
            self.scheme_type == GradingSchemaType.PERCENTAGE
            and self.max_points is not None
        ):
            raise ValueError("max_points must be null for percentage grading schemas.")

        if self.scheme_type == GradingSchemaType.POINTS:
            if self.max_points is None or self.max_points <= 0:
                raise ValueError(
                    "max_points must be provided and > 0 for points grading schemas."
                )

        if self.grade_catalog_code is None and len(self.grades) == 0:
            raise ValueError("Provide either grade_catalog_code or grades.")

        return self


class GradingSchemaGradeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    label: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class GradingSchemaRangeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    grade_id: UUID
    min_value: Decimal
    max_value: Decimal
    min_inclusive: bool
    max_inclusive: bool
    created_at: datetime
    updated_at: datetime


class GradingSchemaOverrideRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    grade_id: UUID
    input_value: Decimal
    created_at: datetime
    updated_at: datetime


class GradingSchemaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    teacher_id: UUID
    name: str
    scheme_type: GradingSchemaType
    max_points: Decimal | None
    is_active: bool
    is_template: bool
    is_system: bool
    source_schema_id: UUID | None
    grades: list[GradingSchemaGradeRead]
    ranges: list[GradingSchemaRangeRead]
    overrides: list[GradingSchemaOverrideRead]
    created_at: datetime
    updated_at: datetime


class GradingSchemaCloneRequest(BaseModel):
    teacher_id: UUID
    name: str | None = Field(default=None, min_length=1, max_length=255)
    as_template: bool = False


class GradingSchemaPromoteToTemplateRequest(BaseModel):
    teacher_id: UUID
    name: str = Field(min_length=1, max_length=255)


class GradingSchemaReplaceTemplateRequest(BaseModel):
    source_schema_id: UUID
