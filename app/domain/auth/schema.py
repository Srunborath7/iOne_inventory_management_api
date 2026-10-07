from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuthCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=1, max_length=191)
    email: str = Field(
        min_length=3,
        max_length=191,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    # Hash this in the service before saving it to Auth.password_hash.
    password: str = Field(min_length=8)


class AuthLogin(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(
        min_length=3,
        max_length=191,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    created_at: datetime
