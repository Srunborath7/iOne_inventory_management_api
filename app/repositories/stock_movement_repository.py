from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.stock_movements.model import StockMovement
from app.repositories.base import BaseRepository


class StockMovementRepository(BaseRepository[StockMovement]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, StockMovement)

    async def list_filtered(
        self, *, product_id: int | None = None, warehouse_id: int | None = None,
        offset: int = 0, limit: int = 100,
    ) -> list[StockMovement]:
        stmt = select(StockMovement)
        if product_id is not None:
            stmt = stmt.where(StockMovement.product_id == product_id)
        if warehouse_id is not None:
            stmt = stmt.where(StockMovement.warehouse_id == warehouse_id)
        result = await self._session.execute(
            stmt.order_by(StockMovement.id.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all())
