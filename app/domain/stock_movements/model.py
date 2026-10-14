from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.domain.auth.model import Auth
    from app.domain.products.model import Product
    from app.domain.warehouses.model import Warehouses


class StockMovement(Base):
    """Immutable record of stock received, sold, adjusted, or returned."""

    __tablename__ = "stock_movements"
    __table_args__ = (
        CheckConstraint("quantity_change <> 0", name="ck_stock_movements_nonzero_quantity"),
        CheckConstraint(
            "movement_type IN ('received', 'sold', 'adjusted', 'returned')",
            name="ck_stock_movements_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity_change: Mapped[int] = mapped_column(Integer, nullable=False)
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("auth_accounts.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    product: Mapped["Product"] = relationship()
    warehouse: Mapped["Warehouses"] = relationship()
    user: Mapped["Auth | None"] = relationship()
