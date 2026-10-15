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
        if order.status not in {"ready", "partially_received", "partially_returned"}:
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

        self._refresh_order_status(order)
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

    async def create_return(
        self,
        *,
        header: dict,
        items: list[dict],
        user_id: int | None,
    ) -> PurchaseReturn:
        order = await self._locked_order(header["purchase_order_id"])
        if order is None:
            raise ValueError("Purchase order not found")
        if order.supplier_id != header["supplier_id"]:
            raise ValueError("Return supplier must match the purchase order supplier")
        if order.warehouse_id is None:
            raise ValueError("Purchase order has no destination warehouse")
        if order.status not in {"received", "partially_received", "partially_returned"}:
            raise ValueError("Only received purchase orders can be returned")

        try:
            await self._apply_return_items(order, items, user_id)
            purchase_return = PurchaseReturn(**header)
            purchase_return.items = [PurchaseReturnItem(**item) for item in items]
            self._session.add(purchase_return)
            self._refresh_order_status(order)
            await self._commit()
        except Exception:
            await self._session.rollback()
            raise
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
        user_id: int | None,
    ) -> PurchaseReturn | None:
        purchase_return = await self._locked_return(return_id)
        if purchase_return is None:
            return None
        order = await self._locked_order(purchase_return.purchase_order_id)
        try:
            if items is not None:
                if order is None:
                    raise ValueError("Cannot replace return items without its purchase order")
                await self._reverse_return_items(order, purchase_return.items, user_id=user_id)
                await self._apply_return_items(order, items, user_id)
                purchase_return.items = [PurchaseReturnItem(**item) for item in items]
            for field, value in changes.items():
                setattr(purchase_return, field, value)
            if order is not None:
                self._refresh_order_status(order)
            await self._commit()
        except Exception:
            await self._session.rollback()
            raise
        return await self.get_return(return_id)

    async def delete_return(self, return_id: int, *, user_id: int | None) -> bool:
        purchase_return = await self._locked_return(return_id)
        if purchase_return is None:
            return False
        order = await self._locked_order(purchase_return.purchase_order_id)
        try:
            if order is not None:
                await self._reverse_return_items(
                    order, purchase_return.items, user_id=user_id
                )
                self._refresh_order_status(order)
            await self._session.delete(purchase_return)
            await self._commit()
        except Exception:
            await self._session.rollback()
            raise
        return True

    async def _locked_order(self, order_id: int | None) -> PurchaseOrder | None:
        if order_id is None:
            return None
        result = await self._session.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.items))
            .where(PurchaseOrder.id == order_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def _locked_return(self, return_id: int) -> PurchaseReturn | None:
        result = await self._session.execute(
            select(PurchaseReturn)
            .options(
                selectinload(PurchaseReturn.items),
                selectinload(PurchaseReturn.supplier),
            )
            .where(PurchaseReturn.id == return_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def _apply_return_items(
        self,
        order: PurchaseOrder,
        items: list[dict],
        user_id: int | None,
    ) -> None:
        lines = {item.id: item for item in order.items}
        product_totals: dict[int, int] = {}
        line_quantities: list[tuple[PurchaseOrderItem, int]] = []
        for item_data in items:
            line = lines.get(item_data["purchase_order_item_id"])
            if line is None or line.product_id != item_data["product_id"]:
                raise ValueError("Return item must match a product line on its purchase order")
            quantity = item_data["quantity"]
            if line.returned_quantity + quantity > line.received_quantity:
                remaining = line.received_quantity - line.returned_quantity
                raise ValueError(f"Purchase order item {line.id} has only {remaining} returnable units")
            product_totals[line.product_id] = product_totals.get(line.product_id, 0) + quantity
            line_quantities.append((line, quantity))

        inventories = {}
        for product_id, quantity in product_totals.items():
            result = await self._session.execute(
                select(WarehousesInventory)
                .where(
                    WarehousesInventory.product_id == product_id,
                    WarehousesInventory.warehouses_id == order.warehouse_id,
                )
                .with_for_update()
            )
            inventory = result.scalar_one_or_none()
            if inventory is None or inventory.quantity < quantity:
                available = inventory.quantity if inventory is not None else 0
                raise ValueError(
                    f"Insufficient warehouse stock to return product {product_id}: "
                    f"requested {quantity}, available {available}"
                )
            inventories[product_id] = inventory

        for product_id, quantity in product_totals.items():
            inventory = inventories[product_id]
            inventory.quantity -= quantity
            inventory.updated_by = user_id
            inventory.is_active = True
        for line, quantity in line_quantities:
            line.returned_quantity += quantity

    async def _reverse_return_items(
        self,
        order: PurchaseOrder,
        items: list[PurchaseReturnItem],
        user_id: int | None,
    ) -> None:
        lines = {item.id: item for item in order.items}
        product_totals: dict[int, int] = {}
        for return_item in items:
            line_id = return_item.purchase_order_item_id
            if line_id is None:
                # Legacy return rows predate purchase-line tracking and did not
                # update inventory, so there is no stock effect to reverse.
                continue
            line = lines.get(line_id)
            if line is None or line.returned_quantity < return_item.quantity:
                raise ValueError("Cannot safely reverse this return's inventory changes")
            if order.warehouse_id is None:
                raise ValueError("Cannot reverse return without the original warehouse")
            line.returned_quantity -= return_item.quantity
            inventory_result = await self._session.execute(
                select(WarehousesInventory)
                .where(
                    WarehousesInventory.product_id == return_item.product_id,
                    WarehousesInventory.warehouses_id == order.warehouse_id,
                )
                .with_for_update()
            )
            inventory = inventory_result.scalar_one_or_none()
            if inventory is not None:
                inventory.updated_by = user_id
            product_totals[return_item.product_id] = (
                product_totals.get(return_item.product_id, 0) + return_item.quantity
            )

        for product_id, quantity in product_totals.items():
            inventory_insert = pg_insert(WarehousesInventory).values(
                product_id=product_id,
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

    @staticmethod
    def _refresh_order_status(order: PurchaseOrder) -> None:
        if any(item.returned_quantity for item in order.items):
            order.status = (
                "returned"
                if all(
                    item.received_quantity == item.ordered_quantity
                    and item.returned_quantity == item.received_quantity
                    for item in order.items
                )
                else "partially_returned"
            )
        elif order.items and all(
            item.received_quantity == item.ordered_quantity for item in order.items
        ):
            order.status = "received"
        elif any(item.received_quantity for item in order.items):
            order.status = "partially_received"

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
