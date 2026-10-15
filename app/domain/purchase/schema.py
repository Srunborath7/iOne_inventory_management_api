from datetime import datetime
from decimal import Decimal

from pydantic import AliasPath, BaseModel, ConfigDict, Field, model_validator


class PurchaseOrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    ordered_quantity: int = Field(gt=0)
    unit_cost: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class PurchaseOrderCreate(BaseModel):
    order_number: str = Field(min_length=1, max_length=50)
    supplier_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    ordered_at: datetime | None = None
    expected_at: datetime | None = None
    note: str | None = None
    items: list[PurchaseOrderItemCreate] = Field(min_length=1)


class PurchaseOrderUpdate(BaseModel):
    order_number: str | None = Field(default=None, min_length=1, max_length=50)
    supplier_id: int | None = Field(default=None, gt=0)
    warehouse_id: int | None = Field(default=None, gt=0)
    expected_at: datetime | None = None
    note: str | None = None
    items: list[PurchaseOrderItemCreate] | None = Field(default=None, min_length=1)


class PurchaseOrderItemResponse(PurchaseOrderItemCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    received_quantity: int
    returned_quantity: int


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    supplier_id: int
    supplier_name: str = Field(validation_alias=AliasPath("supplier", "name"))
    warehouse_id: int | None
    warehouse_name: str | None = Field(
        default=None, validation_alias=AliasPath("warehouse", "name")
    )
    status: str
    ordered_at: datetime
    expected_at: datetime | None
    note: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime
    items: list[PurchaseOrderItemResponse]


class PurchaseOrderReceiptItem(BaseModel):
    item_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class PurchaseOrderReceive(BaseModel):
    items: list[PurchaseOrderReceiptItem] = Field(min_length=1)

    @model_validator(mode="after")
    def item_ids_are_unique(self):
        item_ids = [item.item_id for item in self.items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("Each purchase order item can appear only once per receipt")
        return self


class PurchaseReturnItemCreate(BaseModel):
    purchase_order_item_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    unit_cost: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class PurchaseReturnCreate(BaseModel):
    return_number: str = Field(min_length=1, max_length=50)
    supplier_id: int = Field(gt=0)
    purchase_order_id: int = Field(gt=0)
    returned_at: datetime | None = None
    reason: str | None = None
    items: list[PurchaseReturnItemCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def purchase_order_items_are_unique(self):
        line_ids = [item.purchase_order_item_id for item in self.items]
        if len(line_ids) != len(set(line_ids)):
            raise ValueError("Each purchase order item can appear only once per return")
        return self


class PurchaseReturnUpdate(BaseModel):
    return_number: str | None = Field(default=None, min_length=1, max_length=50)
    returned_at: datetime | None = None
    reason: str | None = None
    items: list[PurchaseReturnItemCreate] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def purchase_order_items_are_unique(self):
        if self.items is not None:
            line_ids = [item.purchase_order_item_id for item in self.items]
            if len(line_ids) != len(set(line_ids)):
                raise ValueError("Each purchase order item can appear only once per return")
        return self


class PurchaseReturnItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_order_item_id: int | None
    product_id: int
    quantity: int
    unit_cost: Decimal


class PurchaseReturnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    return_number: str
    supplier_id: int
    supplier_name: str = Field(validation_alias=AliasPath("supplier", "name"))
    purchase_order_id: int | None
    returned_at: datetime
    reason: str | None
    created_by: int | None
    created_at: datetime
    items: list[PurchaseReturnItemResponse]
