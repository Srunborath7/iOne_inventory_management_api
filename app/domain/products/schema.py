from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

class ProductCreate(BaseModel):
    name: str = Field(min_length=1,max_length=150)
    description: str | None = None
    image_url: str | None = Field(default=None,max_length=255,)
    selling_price: Decimal = Field(gt=0,max_digits=10,decimal_places=2,)
    cost_price: Decimal = Field(gt=0,max_digits=10,decimal_places=2)
    min_stock: int = Field(default=0,ge=0)
    max_stock: int = Field(default=0,ge=0)
    barcode: str = Field(min_length=1,max_length=100)
    brand_id: int
    category_id: int

class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    image_url: str | None = Field(default=None,max_length=255)
    selling_price: Decimal | None = Field(default=None,gt=0,max_digits=10,decimal_places=2)
    cost_price: Decimal | None = Field(default=None,gt=0,max_digits=10,decimal_places=2)
    min_stock: int | None = Field(default=None,ge=0)
    max_stock: int | None = Field(default=None,ge=0)
    barcode: str | None = Field(default=None,min_length=1,max_length=100)
    brand_id: int | None = None
    category_id: int | None = None
    is_active: bool | None = None

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None
    image_url: str | None
    selling_price: Decimal
    cost_price: Decimal
    min_stock: int
    max_stock: int
    barcode: str
    brand_id: int
    category_id: int
    is_active: bool
    created_at: datetime 
    updated_at: datetime
