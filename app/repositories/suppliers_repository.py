from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.suppliers.model import Suppliers
from app.domain.suppliers.schema import SuppliersCreate
from app.repositories.base import BaseRepository


class SuppliersRepository(BaseRepository[Suppliers]):
    """Repository handling database operations for Suppliers entity (OOP - Inheritance)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Suppliers)

    async def get_by_name(self, name: str) -> Suppliers | None:
        """Domain-specific query: find supplier by name."""
        result = await self._session.execute(
            select(Suppliers).where(Suppliers.name == name)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        payload: SuppliersCreate | None = None,
        **attrs: Any,
    ) -> Suppliers:
        """Create a supplier either from schema payload or keyword attributes."""
        if payload is not None:
            attrs = {**payload.model_dump(), **attrs}
        return await super().create(**attrs)
