from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.auth.schema import AuthResponse


class ActivityLogCreate(BaseModel):
    user_id: int | None = None
    action: str = Field(min_length=1, max_length=50)
    entity_type: str = Field(min_length=1, max_length=50)
    entity_id: int | None = None
    description: str | None = None


class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    action: str
    entity_type: str
    entity_id: int | None = None
    description: str | None = None
    created_at: datetime
    user: AuthResponse | None = None
