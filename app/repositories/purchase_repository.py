from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domain.purchase.model import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseReturn,
    PurchaseReturnItem,
)
from app.domain.warehouses_inventory.model import WarehousesInventory


class PurchaseRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def order_number_exists(self, order_number: str) -> bool:
        result = await self._session.execute(
            select(PurchaseOrder.id).where(PurchaseOrder.order_number == order_number)
        )
        return result.scalar_one_or_none() is not None

    async def order_number_exists_for_other(
        self, order_number: str, order_id: int
    ) -> bool:
        result = await self._session.execute(
            select(PurchaseOrder.id).where(
                PurchaseOrder.order_number == order_number,
                PurchaseOrder.id != order_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def return_number_exists(self, return_number: str) -> bool:
        result = await self._session.execute(
            select(PurchaseReturn.id).where(PurchaseReturn.return_number == return_number)
        )
        return result.scalar_one_or_none() is not None

    async def return_number_exists_for_other(
        self, return_number: str, return_id: int
    ) -> bool:
        result = await self._session.execute(
            select(PurchaseReturn.id).where(
                PurchaseReturn.return_number == return_number,
                PurchaseReturn.id != return_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_order(self, *, header: dict, items: list[dict]) -> PurchaseOrder:
        order = PurchaseOrder(**header)
        order.items = [PurchaseOrderItem(**item) for item in items]
        self._session.add(order)
        await self._commit()
        return await self.get_order(order.id)

    async def get_order(self, order_id: int) -> PurchaseOrder | None:
        result = await self._session.execute(
            select(PurchaseOrder)
            .options(
                selectinload(PurchaseOrder.items),
                selectinload(PurchaseOrder.supplier),
                selectinload(PurchaseOrder.warehouse),
            )
            .where(PurchaseOrder.id == order_id)
        )
        return result.scalar_one_or_none()

    async def update_order(
        self,
        order_id: int,
        *,
        changes: dict,
        items: list[dict] | None,
    ) -> PurchaseOrder | None:
        result = await self._session.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.items))
            .where(PurchaseOrder.id == order_id)
            .with_for_update()
        )
        order = result.scalar_one_or_none()
        if order is None:
            return None
        if order.status != "draft":
            raise ValueError("Only draft purchase orders can be edited")
        for field, value in changes.items():
            setattr(order, field, value)
        if items is not None:
            order.items = [PurchaseOrderItem(**item) for item in items]
        await self._commit()
        return await self.get_order(order_id)

    async def delete_order(self, order_id: int) -> bool:
        result = await self._session.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.id == order_id)
            .with_for_update()
        )
        order = result.scalar_one_or_none()
        if order is None:
            return False
        if order.status != "draft":
            raise ValueError("Only draft purchase orders can be deleted")
        await self._session.delete(order)
        await self._commit()
        return True

    async def mark_order_ready(self, order_id: int) -> PurchaseOrder | None:
        result = await self._session.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.items))
            .where(PurchaseOrder.id == order_id)
            .with_for_update()
        )
        order = result.scalar_one_or_none()
        if order is None:
            return None
        if order.status != "draft":
            raise ValueError(f"Cannot mark a purchase order ready from status '{order.status}'")
        order.status = "ready"
        await self._commit()
        return await self.get_order(order_id)

    async def receive_order(
        self,
        order_id: int,
        *,
        item_quantities: dict[int, int],
        user_id: int | None,
    ) -> PurchaseOrder | None:
        result = await self._session.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.items))
            .where(PurchaseOrder.id == order_id)
            .with_for_update()
        )
        order = result.scalar_one_or_none()
        if order is None:
            return None
        if order.status not in {"ready", "partially_received"}:
            raise ValueError("Only ready or partially received purchase orders can be received")
        if order.warehouse_id is None:
            raise ValueError("Purchase order has no destination warehouse")

        order_items = {item.id: item for item in order.items}
        for item_id, quantity in item_quantities.items():
            item = order_items.get(item_id)
            if item is None:
                raise ValueError(f"Purchase order item {item_id} does not belong to this order")
            if item.received_quantity + quantity > item.ordered_quantity:
                remaining = item.ordered_quantity - item.received_quantity
                raise ValueError(
                    f"Item {item_id} can receive at most {remaining} more units"
                )

        for item_id, quantity in item_quantities.items():
            item = order_items[item_id]
            item.received_quantity += quantity
            inventory_insert = pg_insert(WarehousesInventory).values(
                product_id=item.product_id,
                warehouses_id=order.warehouse_id,
                quantity=quantity,
                created_by=user_id,
                updated_by=user_id,
                is_active=True,
            )
            await self._session.execute(
                inventory_insert.on_conflict_do_update(
                    index_elements=["product_id", "warehouses_id"],
                    set_={
                        "quantity": WarehousesInventory.quantity + quantity,
                        "updated_by": user_id,
                        "updated_at": func.now(),
                        "is_active": True,
                    },
                )
            )

        order.status = (
            "received"
            if all(item.received_quantity == item.ordered_quantity for item in order.items)
            else "partially_received"
        )
        await self._commit()
        return await self.get_order(order_id)

    async def list_orders(
        self,
        *,
        supplier_id: int | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PurchaseOrder]:
        stmt = select(PurchaseOrder).options(
            selectinload(PurchaseOrder.items),
            selectinload(PurchaseOrder.supplier),
            selectinload(PurchaseOrder.warehouse),
        )
        if supplier_id is not None:
            stmt = stmt.where(PurchaseOrder.supplier_id == supplier_id)
        if status is not None:
            stmt = stmt.where(PurchaseOrder.status == status)
        result = await self._session.execute(
            stmt.order_by(PurchaseOrder.id.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def create_return(self, *, header: dict, items: list[dict]) -> PurchaseReturn:
        purchase_return = PurchaseReturn(**header)
        purchase_return.items = [PurchaseReturnItem(**item) for item in items]
        self._session.add(purchase_return)
        await self._commit()
        return await self.get_return(purchase_return.id)

    async def get_return(self, return_id: int) -> PurchaseReturn | None:
        result = await self._session.execute(
            select(PurchaseReturn)
            .options(
                selectinload(PurchaseReturn.items),
                selectinload(PurchaseReturn.supplier),
            )
            .where(PurchaseReturn.id == return_id)
        )
        return result.scalar_one_or_none()

    async def update_return(
        self,
        return_id: int,
        *,
        changes: dict,
        items: list[dict] | None,
    ) -> PurchaseReturn | None:
        result = await self._session.execute(
            select(PurchaseReturn)
            .options(
                selectinload(PurchaseReturn.items),
                selectinload(PurchaseReturn.supplier),
            )
            .where(PurchaseReturn.id == return_id)
            .with_for_update()
        )
        purchase_return = result.scalar_one_or_none()
        if purchase_return is None:
            return None
        for field, value in changes.items():
            setattr(purchase_return, field, value)
        if items is not None:
            purchase_return.items = [PurchaseReturnItem(**item) for item in items]
        await self._commit()
        return await self.get_return(return_id)

    async def delete_return(self, return_id: int) -> bool:
        purchase_return = await self._session.get(PurchaseReturn, return_id)
        if purchase_return is None:
            return False
        await self._session.delete(purchase_return)
        await self._commit()
        return True

    async def list_returns(
        self,
        *,
        supplier_id: int | None = None,
        purchase_order_id: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PurchaseReturn]:
        stmt = select(PurchaseReturn).options(
            selectinload(PurchaseReturn.items),
            selectinload(PurchaseReturn.supplier),
        )
        if supplier_id is not None:
            stmt = stmt.where(PurchaseReturn.supplier_id == supplier_id)
        if purchase_order_id is not None:
            stmt = stmt.where(PurchaseReturn.purchase_order_id == purchase_order_id)
        result = await self._session.execute(
            stmt.order_by(PurchaseReturn.id.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def _commit(self) -> None:
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
