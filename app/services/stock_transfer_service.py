from __future__ import annotations

from app.core.exceptions import BadRequest, NotFound
from app.domain.stock_transfers.model import StockTransfer
from app.domain.stock_transfers.schema import StockTransferCreate
from app.repositories.stock_transfer_repository import StockTransferRepository
from app.repositories.warehouses_inventory_repository import WarehousesInventoryRepository
from app.services.base import BaseService


class StockTransferService(BaseService[StockTransferRepository]):
    """
    Business Logic Layer for StockTransfers.

    Orchestrates inventory deduction/addition across warehouses and
    persists an immutable audit record for every movement.
    """

    def __init__(
        self,
        repository: StockTransferRepository,
        inventory_repository: WarehousesInventoryRepository,
    ):
        super().__init__(repository)
        self._inv_repo = inventory_repository

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get(self, transfer_id: int) -> StockTransfer:
        """Fetch a single transfer record by ID or raise NotFound."""
        transfer = await self.repository.get(transfer_id)
        if transfer is None:
            raise NotFound("Stock transfer")
        return transfer

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        product_id: int | None = None,
        warehouse_id: int | None = None,
    ) -> list[StockTransfer]:
        """
        Fetch a paginated, optionally filtered list of transfer records.

        Filters (mutually exclusive, product_id takes priority):
        - product_id   – transfers that moved a specific product
        - warehouse_id – transfers touching a specific warehouse (in or out)
        """
        if product_id is not None:
            return await self.repository.list_by_product(product_id, offset=offset, limit=limit)
        if warehouse_id is not None:
            return await self.repository.list_by_warehouse(warehouse_id, offset=offset, limit=limit)
        return await self.repository.list_all(offset=offset, limit=limit)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def create(
        self,
        data: StockTransferCreate,
        user_id: int | None = None,
    ) -> StockTransfer:
        """
        Execute a warehouse-to-warehouse stock transfer and log it.

        Steps:
        1. Validate input constraints (same-warehouse check, positive qty).
        2. Ensure source inventory exists and has sufficient stock.
        3. Deduct from source; create or top-up destination inventory.
        4. Persist an immutable StockTransfer audit record.
        """
        if data.from_warehouse_id == data.to_warehouse_id:
            raise BadRequest("Source and destination warehouse cannot be the same")

        if data.quantity <= 0:
            raise BadRequest("Transfer quantity must be greater than 0")

        # --- Source inventory -----------------------------------------
        source_inv = await self._inv_repo.get_by_product_and_warehouse(
            product_id=data.product_id,
            warehouses_id=data.from_warehouse_id,
        )
        if source_inv is None or source_inv.quantity < data.quantity:
            available = source_inv.quantity if source_inv else 0
            raise BadRequest(
                f"Insufficient stock in source warehouse: "
                f"requested {data.quantity}, available {available}"
            )

        # --- Destination inventory ------------------------------------
        dest_inv = await self._inv_repo.get_by_product_and_warehouse(
            product_id=data.product_id,
            warehouses_id=data.to_warehouse_id,
        )
        if dest_inv is None:
            await self._inv_repo.create(
                product_id=data.product_id,
                warehouses_id=data.to_warehouse_id,
                quantity=data.quantity,
                created_by=user_id,
                updated_by=user_id,
            )
        else:
            await self._inv_repo.update(
                dest_inv,
                {"quantity": dest_inv.quantity + data.quantity, "updated_by": user_id},
            )

        # --- Deduct source --------------------------------------------
        await self._inv_repo.update(
            source_inv,
            {"quantity": source_inv.quantity - data.quantity, "updated_by": user_id},
        )

        # --- Audit record --------------------------------------------
        return await self.repository.create(
            product_id=data.product_id,
            from_warehouse_id=data.from_warehouse_id,
            to_warehouse_id=data.to_warehouse_id,
            quantity=data.quantity,
            note=data.note,
            created_by=user_id,
        )
