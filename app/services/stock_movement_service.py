from app.core.exceptions import BadRequest, NotFound
from app.domain.stock_movements.model import StockMovement
from app.domain.stock_movements.schema import StockMovementCreate
from app.repositories.stock_movement_repository import StockMovementRepository
from app.repositories.warehouses_inventory_repository import WarehousesInventoryRepository
from app.services.base import BaseService


class StockMovementService(BaseService[StockMovementRepository]):
    def __init__(
        self, repository: StockMovementRepository,
        inventory_repository: WarehousesInventoryRepository,
    ):
        super().__init__(repository)
        self._inventory_repository = inventory_repository

    async def get(self, movement_id: int) -> StockMovement:
        movement = await self.repository.get(movement_id)
        if movement is None:
            raise NotFound("Stock movement")
        return movement

    async def list(
        self, *, product_id: int | None = None, warehouse_id: int | None = None,
        offset: int = 0, limit: int = 100,
    ) -> list[StockMovement]:
        return await self.repository.list_filtered(
            product_id=product_id, warehouse_id=warehouse_id, offset=offset, limit=limit
        )

    async def create(self, data: StockMovementCreate, user_id: int | None = None) -> StockMovement:
        inventory = await self._inventory_repository.get_by_product_and_warehouse(
            product_id=data.product_id, warehouses_id=data.warehouse_id
        )
        if inventory is None:
            if data.quantity_change < 0:
                raise BadRequest("Insufficient stock: no inventory exists for this product and warehouse")
            await self._inventory_repository.create(
                product_id=data.product_id, warehouses_id=data.warehouse_id,
                quantity=data.quantity_change, created_by=user_id, updated_by=user_id,
            )
        else:
            new_quantity = inventory.quantity + data.quantity_change
            if new_quantity < 0:
                raise BadRequest(
                    f"Insufficient stock: current is {inventory.quantity}, "
                    f"change is {data.quantity_change}"
                )
            await self._inventory_repository.update(
                inventory, {"quantity": new_quantity, "updated_by": user_id}
            )

        return await self.repository.create(
            product_id=data.product_id,
            warehouse_id=data.warehouse_id,
            quantity_change=data.quantity_change,
            movement_type=data.movement_type.value,
            reference=data.reference,
            user_id=user_id,
        )
