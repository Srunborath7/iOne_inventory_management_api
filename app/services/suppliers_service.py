from app.services.base import BaseService
from app.repositories.suppliers_repository import SuppliersRepository
from app.domain.suppliers.model import Suppliers
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