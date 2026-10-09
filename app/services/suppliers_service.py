from app.services.base import BaseService
from app.repositories.suppliers_repository import SuppliersRepository
from app.domain.suppliers.model import Suppliers
from app.domain.suppliers.schema import SuppliersCreate, SuppliersUpdate
from app.core.exceptions import BadRequest, Conflict, NotFound

class SuppliersService(BaseService[SuppliersRepository]):
    def __init__(self, repository: SuppliersRepository):
        # Dependency Injection (OOP - Inversion of Control)
        super().__init__(repository)

    async def get(self, suppliers_id: int) -> Suppliers:
        """Fetch a category by ID or raise NotFound."""
        category = await self.repository.get(suppliers_id)
        if category is None:
            raise NotFound("Category")
        return category
    
    async def list(self, *, offset: int = 0, limit: int = 100) -> list[Suppliers]:
        """Fetch a paginated list of categories."""
        return await self.repository.list_all(offset=offset, limit=limit)

    async def create(self, payload: SuppliersCreate) -> Suppliers:
        """Create a supplier from validated request data."""
        return await self.repository.create(payload=payload)

    async def update(self, supplier_id: int, payload: SuppliersUpdate) -> Suppliers:
        """Update a supplier or raise NotFound when it does not exist."""
        supplier = await self.repository.update(
            supplier_id=supplier_id,
            payload=payload,
        )
        if supplier is None:
            raise NotFound("Supplier")
        return supplier

    async def delete(self, supplier_id: int) -> None:
        """Delete a supplier or raise NotFound when it does not exist."""
        deleted = await self.repository.delete(supplier_id)
        if not deleted:
            raise NotFound("Supplier")
