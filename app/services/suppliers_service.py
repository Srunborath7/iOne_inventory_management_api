from __future__ import annotations

from app.core.exceptions import NotFound
from app.domain.suppliers.model import Suppliers
from app.domain.suppliers.schema import SuppliersCreate, SuppliersUpdate
from app.repositories.suppliers_repository import SuppliersRepository
from app.services.base import BaseService


class SuppliersService(BaseService[SuppliersRepository]):
    """Business Logic Layer for Suppliers (OOP - Encapsulation & Separation of Concerns)."""

    def __init__(self, repository: SuppliersRepository):
        super().__init__(repository)

    async def get(self, supplier_id: int) -> Suppliers:
        """Fetch a supplier by ID or raise NotFound."""
        supplier = await self.repository.get(supplier_id)
        if supplier is None:
            raise NotFound("Supplier")
        return supplier

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[Suppliers]:
        """Fetch a paginated list of suppliers."""
        return await self.repository.list_all(offset=offset, limit=limit)

    async def create(self, payload: SuppliersCreate) -> Suppliers:
        """Create a supplier from validated request data."""
        return await self.repository.create(payload=payload)

    async def update(self, supplier_id: int, payload: SuppliersUpdate) -> Suppliers:
        """Update an existing supplier."""
        supplier = await self.get(supplier_id)
        changes = payload.model_dump(exclude_unset=True)
        return await self.repository.update(supplier, changes)

    async def delete(self, supplier_id: int) -> None:
        """Delete a supplier or raise NotFound if not found."""
        supplier = await self.get(supplier_id)
        await self.repository.delete(supplier)
