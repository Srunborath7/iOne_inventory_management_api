from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.brands.model import Brand
from app.repositories.base import BaseRepository


class BrandRepository(BaseRepository[Brand]):
    """Repository handling database operations for Brand entity (OOP - Inheritance)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Brand)

    async def get_by_name(self, name: str) -> Brand | None:
        """Domain-specific query: find brand by unique name."""
        result = await self._session.execute(
            select(Brand).where(Brand.name == name)
        )
        return result.scalar_one_or_none()