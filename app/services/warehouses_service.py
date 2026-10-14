from __future__ import annotations

from app.core.exceptions import Conflict, NotFound
from app.domain.warehouses.model import Warehouses
from app.domain.warehouses.schema import WarehousesCreate, WarehousesUpdate
from app.repositories.warehouses_repository import WarehousesRepository
from app.services.base import BaseService


class WarehouseService(BaseService[WarehousesRepository]):
    """Business Logic Layer for Warehouses (OOP - Encapsulation & Separation of Concerns)."""

    def __init__(self, repository: WarehousesRepository):
        super().__init__(repository)

    async def get(self, warehouse_id: int) -> Warehouses:
        """Fetch a warehouse by ID or raise NotFound."""
        warehouse = await self.repository.get(warehouse_id)
        if warehouse is None:
            raise NotFound("Warehouse")
        return warehouse

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[Warehouses]:
        """Fetch a paginated list of warehouses."""
        return await self.repository.list_all(offset=offset, limit=limit)

    async def create(self, payload: WarehousesCreate) -> Warehouses:
        """Create a new warehouse with uniqueness validation."""
        name = payload.name.strip()
        code = payload.code.strip()

        if await self.repository.get_by_name(name):
            raise Conflict("Warehouse name already exists")
        if await self.repository.get_by_code(code):
            raise Conflict("Warehouse code already exists")

        return await self.repository.create(**payload.model_dump())

    async def update(self, warehouse_id: int, payload: WarehousesUpdate) -> Warehouses:
        """Update an existing warehouse."""
        warehouse = await self.get(warehouse_id)
        changes = payload.model_dump(exclude_unset=True)

        if "name" in changes and changes["name"]:
            name = changes["name"].strip()
            existing = await self.repository.get_by_name(name)
            if existing and existing.id != warehouse_id:
                raise Conflict("Warehouse name already exists")
            changes["name"] = name

        if "code" in changes and changes["code"]:
            code = changes["code"].strip()
            existing_code = await self.repository.get_by_code(code)
            if existing_code and existing_code.id != warehouse_id:
                raise Conflict("Warehouse code already exists")
            changes["code"] = code

        return await self.repository.update(warehouse, changes)

    async def delete(self, warehouse_id: int) -> None:
        """Delete a warehouse or raise NotFound."""
        warehouse = await self.get(warehouse_id)
        await self.repository.delete(warehouse)


# Alias for plural naming compatibility
WarehousesService = WarehouseService