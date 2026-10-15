from app.core.exceptions import Conflict, NotFound
from app.domain.purchase.model import PurchaseOrder, PurchaseReturn
from app.domain.purchase.schema import PurchaseOrderCreate, PurchaseReturnCreate
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
