from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.domain.auth.model import Auth
    from app.domain.products.model import Product
    from app.domain.warehouses.model import Warehouses


class StockTransfer(Base):
    """Immutable audit record of every stock movement between warehouses."""

    __tablename__ = "stock_transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    from_warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    to_warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Optional human-readable note / reason for the transfer
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Who triggered the transfer
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("auth_accounts.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    product: Mapped["Product"] = relationship(foreign_keys=[product_id])
    from_warehouse: Mapped["Warehouses"] = relationship(foreign_keys=[from_warehouse_id])
    to_warehouse: Mapped["Warehouses"] = relationship(foreign_keys=[to_warehouse_id])
    creator: Mapped["Auth | None"] = relationship(foreign_keys=[created_by])
