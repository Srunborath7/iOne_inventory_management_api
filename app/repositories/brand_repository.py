from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.brands.model import Brand
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

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

    async def create(self,*, name: str, desrciption: str| None, image_url: str | None) -> Brand:
        brand = Brand(name = name, desrciption = desrciption, image_url = image_url)
        self.session.add(brand)
        await self._commit()
        await self.session.refresh(brand)
        return brand

    async def _commit(self) -> None:
        try:
            await self.session.commit()
        except InterruptedError:
            await self.session.rollback()
            raise