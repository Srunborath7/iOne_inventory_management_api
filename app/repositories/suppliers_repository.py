from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.suppliers.model import Suppliers
from app.domain.suppliers.schema import SuppliersCreate, SuppliersUpdate

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

    async def create(self, *, payload: SuppliersCreate) -> Suppliers:
        supplier = Suppliers(**payload.model_dump())
        self.session.add(supplier)
        await self._commit()
        await self.session.refresh(supplier)
        return supplier

    async def update( self, *, supplier_id: int, payload: SuppliersUpdate) -> Suppliers | None:
        supplier = await self.get(supplier_id)
        if supplier is None:
            return None

        changes = payload.model_dump(exclude_unset=True)

        for field, value in changes.items():
            setattr(supplier, field, value)

        await self._commit()
        await self.session.refresh(supplier)
        return supplier
    
    async def delete(self, supplier_id: int) -> bool:
        supplier = await self.get(supplier_id)
        if supplier is None:
            return False

        await self.session.delete(supplier)
        await self._commit()
        return True

    async def _commit(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
    
    
