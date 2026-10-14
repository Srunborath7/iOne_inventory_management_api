from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WarehousesInventoryCreate(BaseModel):
    product_id: int = Field(gt=0)
    warehouses_id: int = Field(gt=0)
    quantity: int = Field(default=0, ge=0)
    is_active: bool = True


class WarehousesInventoryUpdate(BaseModel):
    # product_id and warehouses_id are intentionally not updatable.
    quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class WarehousesInventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    warehouses_id: int
    quantity: int
    is_active: bool
    created_by: int | None = None
    updated_by: int | None = None
    created_at: datetime
    updated_at: datetime


class StockTransferRequest(BaseModel):
    from_warehouse_id: int = Field(gt=0)
    to_warehouse_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class StockTransferResponse(BaseModel):
    source_inventory: WarehousesInventoryResponse
    destination_inventory: WarehousesInventoryResponse
    transferred_quantity: int


# Singular aliases
WarehouseInventoryCreate = WarehousesInventoryCreate
WarehouseInventoryUpdate = WarehousesInventoryUpdate
WarehouseInventoryResponse = WarehousesInventoryResponse