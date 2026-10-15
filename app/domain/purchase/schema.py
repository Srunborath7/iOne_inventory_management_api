from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PurchaseOrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    ordered_quantity: int = Field(gt=0)
    received_quantity: int = Field(default=0, ge=0)
    unit_cost: Decimal = Field(ge=0, max_digits=10, decimal_places=2)

    @model_validator(mode="after")
    def received_cannot_exceed_ordered(self):
        if self.received_quantity > self.ordered_quantity:
            raise ValueError("received_quantity cannot exceed ordered_quantity")
        return self


class PurchaseOrderCreate(BaseModel):
    order_number: str = Field(min_length=1, max_length=50)
    supplier_id: int = Field(gt=0)
    status: str = Field(default="draft", min_length=1, max_length=20)
    ordered_at: datetime | None = None
    expected_at: datetime | None = None
    note: str | None = None
    items: list[PurchaseOrderItemCreate] = Field(min_length=1)


class PurchaseOrderItemResponse(PurchaseOrderItemCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    supplier_id: int
    status: str
    ordered_at: datetime
    expected_at: datetime | None
    note: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime
    items: list[PurchaseOrderItemResponse]


class PurchaseReturnItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    unit_cost: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class PurchaseReturnCreate(BaseModel):
    return_number: str = Field(min_length=1, max_length=50)
    supplier_id: int = Field(gt=0)
    purchase_order_id: int | None = Field(default=None, gt=0)
    returned_at: datetime | None = None
    reason: str | None = None
    items: list[PurchaseReturnItemCreate] = Field(min_length=1)


class PurchaseReturnItemResponse(PurchaseReturnItemCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class PurchaseReturnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    return_number: str
    supplier_id: int
    purchase_order_id: int | None
    returned_at: datetime
    reason: str | None
    created_by: int | None
    created_at: datetime
    items: list[PurchaseReturnItemResponse]
