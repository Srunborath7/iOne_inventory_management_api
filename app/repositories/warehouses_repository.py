from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.warehouses.model import Warehouses
from app.repositories.base import BaseRepository


class WarehousesRepository(BaseRepository[Warehouses]):
    """Repository handling database operations for Warehouses entity (OOP - Inheritance)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Warehouses)

    async def get_by_name(self, name: str) -> Warehouses | None:
        """Domain-specific query: find warehouse by name."""
        result = await self._session.execute(
            select(Warehouses).where(Warehouses.name == name)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Warehouses | None:
        """Domain-specific query: find warehouse by unique code."""
        result = await self._session.execute(
            select(Warehouses).where(Warehouses.code == code)
        )
        return result.scalar_one_or_none()