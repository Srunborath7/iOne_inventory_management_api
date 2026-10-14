from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.categories.model import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Repository handling database operations for Category entity (OOP - Inheritance)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Category)

    async def get_by_name(self, name: str) -> Category | None:
        """Domain-specific query: find category by unique name."""
        result = await self._session.execute(
            select(Category).where(Category.name == name)
        )
        return result.scalar_one_or_none()
