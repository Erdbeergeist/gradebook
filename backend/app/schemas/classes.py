from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
