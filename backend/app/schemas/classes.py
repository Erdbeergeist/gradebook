from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.exam_results import ExamResultStatus
from app.models.exams import ExamType, ExamTypeDetail


class ClassCreate(BaseModel):
    teacher_id: UUID
    name: str = Field(min_length=1, max_length=255)


class ClassRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    teacher_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class GradebookStudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str


class GradebookExamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    exam_type: ExamType
    exam_type_detail: ExamTypeDetail | None
    max_points: Decimal
    weight: Decimal
    grading_schema_id: UUID
    created_at: datetime
    updated_at: datetime


class GradebookCellRead(BaseModel):
    student_id: UUID
    exam_id: UUID
    exam_result_id: UUID | None
    points: Decimal | None
    comment: str | None
    status: ExamResultStatus | None
    graded_at: datetime | None
    resolved_input_value: Decimal | None
    resolved_grade_label: str | None


class ClassGradebookRead(BaseModel):
    class_: ClassRead
    students: list[GradebookStudentRead]
    exams: list[GradebookExamRead]
    cells: list[GradebookCellRead]
