from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.products.model import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, product_id: int) -> Product | None:
        return await self.session.get(Product, product_id)

    async def get_by_name(self, name: str) -> Product | None:
        result = await self.session.execute(
            select(Product).where(Product.name == name)
        )
        return result.scalar_one_or_none()

    async def get_by_barcode(self, barcode: str) -> Product | None:
        result = await self.session.execute(
            select(Product).where(Product.barcode == barcode)
        )
        return result.scalar_one_or_none()

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[Product]:
        result = await self.session.execute(
            select(Product).order_by(Product.id).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def list_all(self, *, offset: int = 0, limit: int = 100) -> list[Product]:
        return await self.list(offset=offset, limit=limit)

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
        product = Product(
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
        self.session.add(product)
        await self._commit()
        await self.session.refresh(product)
        return product

    async def update(self, product: Product, changes: dict) -> Product:
        for field, value in changes.items():
            setattr(product, field, value)
        await self._commit()
        await self.session.refresh(product)
        return product

    async def delete(self, product: Product) -> None:
        await self.session.delete(product)
        await self._commit()

    async def _commit(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
