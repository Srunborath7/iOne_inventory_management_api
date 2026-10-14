from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.stock_transfers.model import StockTransfer
from app.repositories.base import BaseRepository


class StockTransferRepository(BaseRepository[StockTransfer]):
    """Repository for StockTransfer: insert-only audit log."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, StockTransfer)

    async def list_by_product(
        self, product_id: int, *, offset: int = 0, limit: int = 100
    ) -> list[StockTransfer]:
        """All transfers that involve a specific product."""
        result = await self._session.execute(
            select(StockTransfer)
            .where(StockTransfer.product_id == product_id)
            .order_by(StockTransfer.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_warehouse(
        self, warehouse_id: int, *, offset: int = 0, limit: int = 100
    ) -> list[StockTransfer]:
        """All transfers that touch a specific warehouse (source or destination)."""
        result = await self._session.execute(
            select(StockTransfer)
            .where(
                (StockTransfer.from_warehouse_id == warehouse_id)
                | (StockTransfer.to_warehouse_id == warehouse_id)
            )
            .order_by(StockTransfer.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_all(
        self, *, offset: int = 0, limit: int = 100, order_by=None
    ) -> list[StockTransfer]:
        """Fetch all transfers ordered by newest first."""
        result = await self._session.execute(
            select(StockTransfer)
            .order_by(StockTransfer.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
