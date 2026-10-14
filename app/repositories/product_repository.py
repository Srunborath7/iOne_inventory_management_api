from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.products.model import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Repository handling database operations for Product entity (OOP - Inheritance)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Product)

    async def get(self, item_id: int) -> Product | None:
        """Fetch a single product by ID with inventories preloaded for total_quantity calculation."""
        result = await self._session.execute(
            select(Product)
            .options(selectinload(Product.inventories))
            .where(Product.id == item_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: Any = None,
    ) -> list[Product]:
        """Fetch a paginated list of products with inventories preloaded."""
        stmt = select(Product).options(selectinload(Product.inventories))
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        else:
            stmt = stmt.order_by(Product.id)
        stmt = stmt.offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Product | None:
        """Domain-specific query: find product by unique name."""
        result = await self._session.execute(
            select(Product).where(Product.name == name)
        )
        return result.scalar_one_or_none()

    async def get_by_barcode(self, barcode: str) -> Product | None:
        """Domain-specific query: find product by barcode."""
        result = await self._session.execute(
            select(Product).where(Product.barcode == barcode)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        image_url: str | None = None,
        selling_price: Decimal,
        cost_price: Decimal,
        min_stock: int = 0,
        max_stock: int = 0,
        barcode: str,
        brand_id: int,
        category_id: int,
        created_by: int | None = None,
        updated_by: int | None = None,
        is_active: bool = True,
    ) -> Product:
        """Create and persist a product using base repository transaction management."""
        return await super().create(
            name=name,
            description=description,
            image_url=image_url,
            selling_price=selling_price,
            cost_price=cost_price,
            min_stock=min_stock,
            max_stock=max_stock,
            barcode=barcode,
            brand_id=brand_id,
            category_id=category_id,
            created_by=created_by,
            updated_by=updated_by,
            is_active=is_active,
        )
