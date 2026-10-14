from __future__ import annotations

from app.core.exceptions import BadRequest, Conflict, NotFound
from app.domain.warehouses_inventory.model import WarehousesInventory
from app.domain.warehouses_inventory.schema import (
    WarehousesInventoryCreate,
    WarehousesInventoryUpdate,
)
from app.repositories.warehouses_inventory_repository import (
    WarehousesInventoryRepository,
)
from app.services.base import BaseService


class WarehousesInventoryService(BaseService[WarehousesInventoryRepository]):
    """Business Logic Layer for WarehousesInventory (OOP - Encapsulation & Separation of Concerns)."""

    def __init__(self, repository: WarehousesInventoryRepository):
        super().__init__(repository)

    async def get(self, inventory_id: int) -> WarehousesInventory:
        """Fetch an inventory record by ID or raise NotFound."""
        inventory = await self.repository.get(inventory_id)
        if inventory is None:
            raise NotFound("Warehouse inventory")
        return inventory

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        product_id: int | None = None,
        warehouses_id: int | None = None,
    ) -> list[WarehousesInventory]:
        """Fetch a paginated list of inventory records with optional product/warehouse filters."""
        if product_id is not None:
            return await self.repository.list_by_product(product_id, offset=offset, limit=limit)
        if warehouses_id is not None:
            return await self.repository.list_by_warehouse(warehouses_id, offset=offset, limit=limit)
        return await self.repository.list_all(offset=offset, limit=limit)

    async def create(
        self,
        data: WarehousesInventoryCreate,
        user_id: int | None = None,
    ) -> WarehousesInventory:
        """Create a new warehouse inventory record with unique constraint validation."""
        existing = await self.repository.get_by_product_and_warehouse(
            product_id=data.product_id,
            warehouses_id=data.warehouses_id,
        )
        if existing:
            raise Conflict("Inventory record already exists for this product in this warehouse")

        return await self.repository.create(
            product_id=data.product_id,
            warehouses_id=data.warehouses_id,
            quantity=data.quantity,
            is_active=data.is_active,
            created_by=user_id,
            updated_by=user_id,
        )

    async def update(
        self,
        inventory_id: int,
        data: WarehousesInventoryUpdate,
        user_id: int | None = None,
    ) -> WarehousesInventory:
        """Update an inventory record (e.g. adjust quantity or active status)."""
        inventory = await self.get(inventory_id)
        changes = data.model_dump(exclude_unset=True)

        if "quantity" in changes and changes["quantity"] is not None:
            if changes["quantity"] < 0:
                raise BadRequest("Quantity cannot be negative")

        if user_id is not None:
            changes["updated_by"] = user_id

        return await self.repository.update(inventory, changes)

    async def adjust_stock(
        self,
        inventory_id: int,
        delta: int,
        user_id: int | None = None,
    ) -> WarehousesInventory:
        """Adjust inventory stock by a positive or negative quantity."""
        inventory = await self.get(inventory_id)
        new_quantity = inventory.quantity + delta
        if new_quantity < 0:
            raise BadRequest(f"Insufficient stock: current is {inventory.quantity}, change is {delta}")

        changes = {"quantity": new_quantity}
        if user_id is not None:
            changes["updated_by"] = user_id

        return await self.repository.update(inventory, changes)

    async def transfer_stock(
        self,
        *,
        from_warehouse_id: int,
        to_warehouse_id: int,
        product_id: int,
        quantity: int,
        user_id: int | None = None,
    ) -> tuple[WarehousesInventory, WarehousesInventory]:
        """Transfer stock of a product from one warehouse to another."""
        if from_warehouse_id == to_warehouse_id:
            raise BadRequest("Source and destination warehouse cannot be the same")
        if quantity <= 0:
            raise BadRequest("Transfer quantity must be greater than 0")

        source_inv = await self.repository.get_by_product_and_warehouse(
            product_id=product_id,
            warehouses_id=from_warehouse_id,
        )
        if source_inv is None or source_inv.quantity < quantity:
            available = source_inv.quantity if source_inv else 0
            raise BadRequest(
                f"Insufficient stock in source warehouse: requested {quantity}, available {available}"
            )

        dest_inv = await self.repository.get_by_product_and_warehouse(
            product_id=product_id,
            warehouses_id=to_warehouse_id,
        )
        if dest_inv is None:
            dest_inv = await self.repository.create(
                product_id=product_id,
                warehouses_id=to_warehouse_id,
                quantity=quantity,
                created_by=user_id,
                updated_by=user_id,
            )
        else:
            await self.repository.update(
                dest_inv,
                {"quantity": dest_inv.quantity + quantity, "updated_by": user_id},
            )

        await self.repository.update(
            source_inv,
            {"quantity": source_inv.quantity - quantity, "updated_by": user_id},
        )

        return source_inv, dest_inv

    async def delete(self, inventory_id: int) -> None:
        """Delete an inventory record."""
        inventory = await self.get(inventory_id)
        await self.repository.delete(inventory)


# Alias for singular naming
WarehouseInventoryService = WarehousesInventoryService
