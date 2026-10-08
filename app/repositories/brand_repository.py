from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.brands.model import Brand
from app.repositories.base import BaseRepository


class BrandRepository(BaseRepository[Brand]):
    """Repository handling database operations for Brand entity."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Brand)

    async def get_by_name(self, name: str) -> Brand | None:
        """Find brand by unique name."""
        result = await self.session.execute(
            select(Brand).where(Brand.name == name)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        image_url: str | None = None,
    ) -> Brand:
        """Create a new brand record."""
        return await super().create(
            name=name,
            description=description,
            image_url=image_url,
        )