from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuthCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=191)
    email: str = Field(min_length=1, max_length=191)
    # Hash this in the service before saving it to Auth.password_hash.
    password: str = Field(min_length=8)


class AuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    created_at: datetime
