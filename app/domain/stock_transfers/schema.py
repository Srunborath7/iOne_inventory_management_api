from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StockTransferCreate(BaseModel):
    from_warehouse_id: int = Field(gt=0, description="Source warehouse ID")
    to_warehouse_id: int = Field(gt=0, description="Destination warehouse ID")
    product_id: int = Field(gt=0, description="Product ID to transfer")
    quantity: int = Field(gt=0, description="Number of units to transfer")
    note: str | None = Field(default=None, max_length=500, description="Optional reason / note")


class StockTransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    from_warehouse_id: int
    to_warehouse_id: int
    quantity: int
    note: str | None = None
    created_by: int | None = None
    created_at: datetime
