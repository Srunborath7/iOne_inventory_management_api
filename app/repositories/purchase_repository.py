from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.purchase.model import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseReturn,
    PurchaseReturnItem,
)


class PurchaseRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def order_number_exists(self, order_number: str) -> bool:
        result = await self._session.execute(
            select(PurchaseOrder.id).where(PurchaseOrder.order_number == order_number)
        )
        return result.scalar_one_or_none() is not None

    async def return_number_exists(self, return_number: str) -> bool:
        result = await self._session.execute(
            select(PurchaseReturn.id).where(PurchaseReturn.return_number == return_number)
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
            .options(selectinload(PurchaseOrder.items))
            .where(PurchaseOrder.id == order_id)
        )
        return result.scalar_one_or_none()

    async def list_orders(
        self,
        *,
        supplier_id: int | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PurchaseOrder]:
        stmt = select(PurchaseOrder).options(selectinload(PurchaseOrder.items))
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
            .options(selectinload(PurchaseReturn.items))
            .where(PurchaseReturn.id == return_id)
        )
        return result.scalar_one_or_none()

    async def list_returns(
        self,
        *,
        supplier_id: int | None = None,
        purchase_order_id: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PurchaseReturn]:
        stmt = select(PurchaseReturn).options(selectinload(PurchaseReturn.items))
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
