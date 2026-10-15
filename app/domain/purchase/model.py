from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
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
    from app.domain.products.model import Product
    from app.domain.suppliers.model import Suppliers


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", server_default="draft")
    ordered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("auth_accounts.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    supplier: Mapped["Suppliers"] = relationship()
    creator: Mapped["Auth | None"] = relationship()
    items: Mapped[list[PurchaseOrderItem]] = relationship(
        back_populates="purchase_order", cascade="all, delete-orphan"
    )


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    __table_args__ = (
        CheckConstraint("ordered_quantity > 0", name="ck_purchase_order_items_ordered_positive"),
        CheckConstraint("received_quantity >= 0", name="ck_purchase_order_items_received_nonnegative"),
        CheckConstraint("received_quantity <= ordered_quantity", name="ck_purchase_order_items_received_lte_ordered"),
        CheckConstraint("unit_cost >= 0", name="ck_purchase_order_items_unit_cost_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    ordered_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    received_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    purchase_order: Mapped[PurchaseOrder] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class PurchaseReturn(Base):
    __tablename__ = "purchase_returns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    return_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    purchase_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"), index=True
    )
    returned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    reason: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("auth_accounts.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    supplier: Mapped["Suppliers"] = relationship()
    purchase_order: Mapped[PurchaseOrder | None] = relationship()
    creator: Mapped["Auth | None"] = relationship()
    items: Mapped[list[PurchaseReturnItem]] = relationship(
        back_populates="purchase_return", cascade="all, delete-orphan"
    )


class PurchaseReturnItem(Base):
    __tablename__ = "purchase_return_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_purchase_return_items_quantity_positive"),
        CheckConstraint("unit_cost >= 0", name="ck_purchase_return_items_unit_cost_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_return_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_returns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    purchase_return: Mapped[PurchaseReturn] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()
