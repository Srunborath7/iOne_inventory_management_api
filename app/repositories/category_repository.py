from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.catgories.model import Category


class CategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, category_id: int) -> Category | None:
        return await self.session.get(Category, category_id)

    async def get_by_name(self, name: str) -> Category | None:
        result = await self.session.execute(
            select(Category).where(Category.name == name)
        )
        return result.scalar_one_or_none()

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[Category]:
        result = await self.session.execute(
            select(Category).order_by(Category.id).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        name: str,
        description: str | None,
        image_url: str | None,
    ) -> Category:
        category = Category(
            name=name,
            description=description,
            image_url=image_url,
        )
        self.session.add(category)
        await self._commit()
        await self.session.refresh(category)
        return category

    async def update(self, category: Category, changes: dict) -> Category:
        for field, value in changes.items():
            setattr(category, field, value)
        await self._commit()
        await self.session.refresh(category)
        return category

    async def delete(self, category: Category) -> None:
        await self.session.delete(category)
        await self._commit()

    async def _commit(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
