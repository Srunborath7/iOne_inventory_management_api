from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.suppliers.model import Suppliers

class SuppliersRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, suppliers_id: int) ->Suppliers | None:
        return await self.session.get(Suppliers, suppliers_id)

    async def get_by_name(self, name: str) -> Suppliers | None:
        result = await self.session.execute(
            select(Suppliers).where(Suppliers.name == name)
        )
        return result.scalar_one_or_none()

    async def list_all(self, *, offset: int = 0, limit: int = 100) -> list[Suppliers]:
        result = await self.session.execute(
            select(Suppliers).order_by(Suppliers.id).offset(offset).limit(limit)
        )
        return list(result.scalars().all())
    