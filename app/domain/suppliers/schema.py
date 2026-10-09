from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SuppliersCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    age: int = Field(ge=10, le=99)
    gender: Literal["male", "female", "other"]
    contact: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=15)
    address: str | None = Field(default=None, max_length=150)
    is_active: bool = True
    note: str | None = None


class SuppliersUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    age: int | None = Field(default=None, ge=10, le=99)
    gender: Literal["male", "female", "other"] | None = None
    contact: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=15)
    address: str | None = Field(default=None, max_length=150)
    is_active: bool | None = None
    note: str | None = None


class SuppliersResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    gender: str
    contact: str | None = None
    phone: str | None = None
    address: str | None = None
    is_active: bool
    note: str | None = None
    created_at: datetime
    updated_at: datetime