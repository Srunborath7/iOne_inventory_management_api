from app.core.exceptions import BadRequest, Conflict, NotFound
from app.domain.purchase.model import PurchaseOrder, PurchaseReturn
from app.domain.purchase.schema import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseReturnCreate,
    PurchaseReturnUpdate,
)
from app.repositories.purchase_repository import PurchaseRepository
from app.services.base import BaseService


class PurchaseService(BaseService[PurchaseRepository]):
    async def create_order(
        self, data: PurchaseOrderCreate, user_id: int | None = None
    ) -> PurchaseOrder:
        if await self.repository.order_number_exists(data.order_number):
            raise Conflict("Purchase order number already exists")
        values = data.model_dump(exclude={"items", "ordered_at"})
        if data.ordered_at is not None:
            values["ordered_at"] = data.ordered_at
        values["created_by"] = user_id
        return await self.repository.create_order(
            header=values,
            items=[item.model_dump() for item in data.items],
        )

    async def get_order(self, order_id: int) -> PurchaseOrder:
        order = await self.repository.get_order(order_id)
        if order is None:
            raise NotFound("Purchase order")
        return order

    async def mark_order_ready(self, order_id: int) -> PurchaseOrder:
        try:
            order = await self.repository.mark_order_ready(order_id)
        except ValueError as exc:
            raise BadRequest(str(exc)) from exc
        if order is None:
            raise NotFound("Purchase order")
        return order

    async def update_order(
        self, order_id: int, data: PurchaseOrderUpdate
    ) -> PurchaseOrder:
        changes = data.model_dump(exclude_unset=True)
        items = changes.pop("items", None)
        if not changes and items is None:
            raise BadRequest("Provide at least one field to update")
        for field in ("order_number", "supplier_id", "warehouse_id"):
            if field in changes and changes[field] is None:
                raise BadRequest(f"{field} cannot be null")
        if "order_number" in changes and await self.repository.order_number_exists_for_other(
            changes["order_number"], order_id
        ):
            raise Conflict("Purchase order number already exists")
        item_values = None if items is None else [item.model_dump() for item in items]
        try:
            order = await self.repository.update_order(
                order_id, changes=changes, items=item_values
            )
        except ValueError as exc:
            raise BadRequest(str(exc)) from exc
        if order is None:
            raise NotFound("Purchase order")
        return order

    async def delete_order(self, order_id: int) -> None:
        try:
            deleted = await self.repository.delete_order(order_id)
        except ValueError as exc:
            raise BadRequest(str(exc)) from exc
        if not deleted:
            raise NotFound("Purchase order")

    async def receive_order(
        self,
        order_id: int,
        item_quantities: dict[int, int],
        user_id: int | None,
    ) -> PurchaseOrder:
        try:
            order = await self.repository.receive_order(
                order_id,
                item_quantities=item_quantities,
                user_id=user_id,
            )
        except ValueError as exc:
            raise BadRequest(str(exc)) from exc
        if order is None:
            raise NotFound("Purchase order")
        return order

    async def list_orders(
        self,
        *,
        supplier_id: int | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PurchaseOrder]:
        return await self.repository.list_orders(
            supplier_id=supplier_id, status=status, offset=offset, limit=limit
        )

    async def create_return(
        self, data: PurchaseReturnCreate, user_id: int | None = None
    ) -> PurchaseReturn:
        if await self.repository.return_number_exists(data.return_number):
            raise Conflict("Purchase return number already exists")
        values = data.model_dump(exclude={"items", "returned_at"})
        if data.returned_at is not None:
            values["returned_at"] = data.returned_at
        values["created_by"] = user_id
        return await self.repository.create_return(
            header=values,
            items=[item.model_dump() for item in data.items],
        )

    async def update_return(
        self, return_id: int, data: PurchaseReturnUpdate
    ) -> PurchaseReturn:
        changes = data.model_dump(exclude_unset=True)
        items = changes.pop("items", None)
        if not changes and items is None:
            raise BadRequest("Provide at least one field to update")
        for field in ("return_number", "supplier_id"):
            if field in changes and changes[field] is None:
                raise BadRequest(f"{field} cannot be null")
        if "return_number" in changes and await self.repository.return_number_exists_for_other(
            changes["return_number"], return_id
        ):
            raise Conflict("Purchase return number already exists")
        item_values = None if items is None else [item.model_dump() for item in items]
        purchase_return = await self.repository.update_return(
            return_id, changes=changes, items=item_values
        )
        if purchase_return is None:
            raise NotFound("Purchase return")
        return purchase_return

    async def delete_return(self, return_id: int) -> None:
        if not await self.repository.delete_return(return_id):
            raise NotFound("Purchase return")

    async def get_return(self, return_id: int) -> PurchaseReturn:
        purchase_return = await self.repository.get_return(return_id)
        if purchase_return is None:
            raise NotFound("Purchase return")
        return purchase_return

    async def list_returns(
        self,
        *,
        supplier_id: int | None = None,
        purchase_order_id: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PurchaseReturn]:
        return await self.repository.list_returns(
            supplier_id=supplier_id,
            purchase_order_id=purchase_order_id,
            offset=offset,
            limit=limit,
        )
