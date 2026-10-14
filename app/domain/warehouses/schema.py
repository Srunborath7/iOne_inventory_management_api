from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WarehousesCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    code: str = Field(min_length=1, max_length=50)
    address: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool = True


class WarehousesUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    address: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class WarehousesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    address: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Aliases for singular naming
WarehouseCreate = WarehousesCreate
WarehouseUpdate = WarehousesUpdate
WarehouseResponse = WarehousesResponse