from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeacherCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class TeacherRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    user_id: UUID | None
    name: str
    created_at: datetime
    updated_at: datetime
