from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.auth.model import Auth
from app.domain.products.model import Product
from app.domain.warehouses.model import Warehouses
from app.domain.warehouses_inventory.model import WarehousesInventory
from app.repositories.base import BaseRepository


class WarehousesInventoryRepository(BaseRepository[WarehousesInventory]):
    """Repository handling database operations for WarehousesInventory (OOP - Inheritance)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, WarehousesInventory)

    async def get_by_product_and_warehouse(
        self, product_id: int, warehouses_id: int
    ) -> WarehousesInventory | None:
        """Find an inventory record for a specific product in a specific warehouse."""
        result = await self._session.execute(
            select(WarehousesInventory).where(
                WarehousesInventory.product_id == product_id,
                WarehousesInventory.warehouses_id == warehouses_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_warehouse(
        self, warehouses_id: int, *, offset: int = 0, limit: int = 100
    ) -> list[WarehousesInventory]:
        """Fetch all inventory records for a specific warehouse."""
        result = await self._session.execute(
            select(WarehousesInventory)
            .where(WarehousesInventory.warehouses_id == warehouses_id)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_product(
        self, product_id: int, *, offset: int = 0, limit: int = 100
    ) -> list[WarehousesInventory]:
        """Fetch all warehouse stock locations for a specific product."""
        result = await self._session.execute(
            select(WarehousesInventory)
            .where(WarehousesInventory.product_id == product_id)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_product_name(self, name: str) -> WarehousesInventory | None:
        """Find warehouse inventory by product name (joins Product)."""
        result = await self._session.execute(
            select(WarehousesInventory)
            .join(WarehousesInventory.product)
            .where(Product.name == name)
        )
        return result.scalar_one_or_none()

    async def get_by_warehouses_name(self, name: str) -> WarehousesInventory | None:
        """Find warehouse inventory by warehouse name (joins Warehouses)."""
        result = await self._session.execute(
            select(WarehousesInventory)
            .join(WarehousesInventory.warehouses)
            .where(Warehouses.name == name)
        )
        return result.scalar_one_or_none()

    async def get_by_creator_name(self, name: str) -> WarehousesInventory | None:
        """Find warehouse inventory by creator full name (joins Auth)."""
        result = await self._session.execute(
            select(WarehousesInventory)
            .join(WarehousesInventory.creator)
            .where(Auth.full_name == name)
        )
        return result.scalar_one_or_none()


# Alias for singular naming
WarehouseInventoryRepository = WarehousesInventoryRepository