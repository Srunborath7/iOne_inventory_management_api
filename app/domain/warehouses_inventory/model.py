from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BOOLEAN,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.domain.auth.model import Auth
    from app.domain.products.model import Product
    from app.domain.warehouses.model import Warehouses


class WarehousesInventory(Base):
    __tablename__ = "warehouse_inventory"
    __table_args__ = (
        UniqueConstraint("product_id", "warehouses_id", name="uq_inventory_product_warehouse"),
        CheckConstraint("quantity >= 0", name="ck_inventory_quantity_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouses_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("auth_accounts.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    updated_by: Mapped[int | None] = mapped_column(
        ForeignKey("auth_accounts.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(BOOLEAN, default=True, nullable=False)

    # Relationships
    product: Mapped["Product"] = relationship(back_populates="inventories")
    warehouses: Mapped["Warehouses"] = relationship(back_populates="inventories")
    creator: Mapped["Auth | None"] = relationship(foreign_keys=[created_by])
    updater: Mapped["Auth | None"] = relationship(foreign_keys=[updated_by])


# Aliases for singular naming
WarehouseInventory = WarehousesInventory