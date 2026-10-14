from __future__ import annotations

from app.core.exceptions import NotFound
from app.domain.customers.model import Customers
from app.domain.customers.schema import CustomersCreate, CustomersUpdate
from app.repositories.customers_repository import CustomersRepository
from app.services.base import BaseService


class CustomersService(BaseService[CustomersRepository]):
    """Business Logic Layer for Customers (OOP - Encapsulation & Separation of Concerns)."""

    def __init__(self, repository: CustomersRepository):
        super().__init__(repository)

    async def get(self, customer_id: int) -> Customers:
        """Fetch a customer by ID or raise NotFound."""
        customer = await self.repository.get(customer_id)
        if customer is None:
            raise NotFound("customer")
        return customer

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[Customers]:
        """Fetch a paginated list of Customers."""
        return await self.repository.list_all(offset=offset, limit=limit)

    async def create(self, payload: CustomersCreate) -> Customers:
        """Create a customer from validated request data."""
        return await self.repository.create(payload=payload)

    async def update(self, customer_id: int, payload: CustomersUpdate) -> Customers:
        """Update an existing customer."""
        customer = await self.get(customer_id)
        changes = payload.model_dump(exclude_unset=True)
        return await self.repository.update(customer, changes)

    async def delete(self, customer_id: int) -> None:
        """Delete a customer or raise NotFound if not found."""
        customer = await self.get(customer_id)
        await self.repository.delete(customer)
