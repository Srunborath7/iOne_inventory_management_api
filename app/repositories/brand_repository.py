from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.brands.model import Brand


class BrandRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, brand_id: int) -> Brand | None:
        return await self.session.get(Brand, brand_id)

    async def get_by_name(self, name: str) -> Brand | None:
        result = await self.session.execute(
            select(Brand).where(Brand.name == name)
        )
        return result.scalar_one_or_none()

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[Brand]:
        result = await self.session.execute(
            select(Brand).order_by(Brand.id).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def list_all(self, *, offset: int = 0, limit: int = 100) -> list[Brand]:
        return await self.list(offset=offset, limit=limit)

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        image_url: str | None = None,
    ) -> Brand:
        brand = Brand(
            name=name,
            description=description,
            image_url=image_url,
        )
        self.session.add(brand)
        await self._commit()
        await self.session.refresh(brand)
        return brand

    async def update(self, brand: Brand, changes: dict) -> Brand:
        for field, value in changes.items():
            setattr(brand, field, value)
        await self._commit()
        await self.session.refresh(brand)
        return brand

    async def delete(self, brand: Brand) -> None:
        await self.session.delete(brand)
        await self._commit()

    async def _commit(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise