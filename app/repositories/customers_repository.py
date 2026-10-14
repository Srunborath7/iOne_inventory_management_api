from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.customers.model import Customers
from app.domain.customers.schema import CustomersCreate
from app.repositories.base import BaseRepository


class CustomersRepository(BaseRepository[Customers]):
    """Repository handling database operations for Suppliers entity (OOP - Inheritance)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Customers)

    async def get_by_name(self, name: str) -> Customers | None:
        """Domain-specific query: find supplier by name."""
        result = await self._session.execute(
            select(Customers).where(Customers.name == name)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        payload: CustomersCreate | None = None,
        **attrs: Any,
    ) -> Customers:
        """Create a supplier either from schema payload or keyword attributes."""
        if payload is not None:
            attrs = {**payload.model_dump(), **attrs}
        return await super().create(**attrs)
