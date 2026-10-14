from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BOOLEAN,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.domain.auth.model import Auth
    from app.domain.brands.model import Brand
    from app.domain.categories.model import Category
    from app.domain.warehouses_inventory.model import WarehousesInventory


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Stock threshold
    min_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Product identification
    barcode: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    # Foreign Keys
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("auth_accounts.id", ondelete="RESTRICT"), nullable=True, index=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("auth_accounts.id", ondelete="RESTRICT"), nullable=True, index=True)

    # Status
    is_active: Mapped[bool] = mapped_column(BOOLEAN, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    brand: Mapped["Brand"] = relationship(back_populates="products")
    category: Mapped["Category"] = relationship(back_populates="products")
    creator: Mapped["Auth | None"] = relationship(foreign_keys=[created_by])
    updater: Mapped["Auth | None"] = relationship(foreign_keys=[updated_by])
    inventories: Mapped[list["WarehousesInventory"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )

    @property
    def total_quantity(self) -> int:
        """Calculate total stock across all active warehouse inventories."""
        inv_list = getattr(self, "inventories", None)
        if not inv_list:
            return 0
        return sum(inv.quantity for inv in inv_list if getattr(inv, "is_active", True))

    @property
    def stock_status(self) -> str:
        """Check stock health against min/max thresholds."""
        qty = self.total_quantity
        if qty == 0:
            return "OUT_OF_STOCK"
        if qty <= self.min_stock:
            return "LOW_STOCK"
        if self.max_stock > 0 and qty > self.max_stock:
            return "OVERSTOCKED"
        return "IN_STOCK"