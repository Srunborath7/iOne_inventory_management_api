from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MovementType(StrEnum):
    RECEIVED = "received"
    SOLD = "sold"
    ADJUSTED = "adjusted"
    RETURNED = "returned"


class StockMovementCreate(BaseModel):
    product_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    quantity_change: int = Field(description="Signed quantity change")
    movement_type: MovementType
    reference: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_change(self):
        if self.quantity_change == 0:
            raise ValueError("quantity_change must not be zero")
        if self.movement_type in (MovementType.RECEIVED, MovementType.RETURNED) and self.quantity_change < 0:
            raise ValueError(f"{self.movement_type.value} movements must increase stock")
        if self.movement_type == MovementType.SOLD and self.quantity_change > 0:
            raise ValueError("sold movements must decrease stock")
        return self


class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    warehouse_id: int
    quantity_change: int
    movement_type: MovementType
    reference: str | None
    user_id: int | None
    created_at: datetime
