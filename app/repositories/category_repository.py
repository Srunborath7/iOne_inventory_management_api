from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.categories.model import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Repository handling database operations for Category entity."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Category)

    async def get_by_name(self, name: str) -> Category | None:
        """Find category by unique name."""
        result = await self.session.execute(
            select(Category).where(Category.name == name)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        image_url: str | None = None,
    ) -> Category:
        """Create a new category record."""
        return await super().create(
            name=name,
            description=description,
            image_url=image_url,
        )
