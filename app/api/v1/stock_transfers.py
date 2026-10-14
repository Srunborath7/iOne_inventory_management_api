from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_account
from app.core.database import get_db
from app.domain.auth.model import Auth
from app.domain.stock_transfers.schema import StockTransferCreate, StockTransferResponse
from app.repositories.stock_transfer_repository import StockTransferRepository
from app.repositories.warehouses_inventory_repository import WarehousesInventoryRepository
from app.services.stock_transfer_service import StockTransferService

router = APIRouter(
    prefix="/stock-transfers",
    tags=["Stock Transfers"],
    dependencies=[Depends(get_current_account)],
)


def get_service(session: Annotated[AsyncSession, Depends(get_db)]) -> StockTransferService:
    return StockTransferService(
        StockTransferRepository(session),
        WarehousesInventoryRepository(session),
    )


ServiceDep = Annotated[StockTransferService, Depends(get_service)]


@router.post("", response_model=StockTransferResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_transfer(
    payload: StockTransferCreate,
    service: ServiceDep,
    current_account: Annotated[Auth, Depends(get_current_account)],
) -> StockTransferResponse:
    """
    Transfer stock of a product from one warehouse to another.

    - Validates sufficient stock in the source warehouse.
    - Auto-creates destination inventory record if it doesn't exist yet.
    - Persists an immutable audit record and returns it.
    """
    return await service.create(payload, user_id=current_account.id)


@router.get("", response_model=list[StockTransferResponse])
async def list_stock_transfers(
    service: ServiceDep,
    product_id: int | None = Query(default=None, description="Filter by product ID"),
    warehouse_id: int | None = Query(
        default=None, description="Filter by warehouse ID (source OR destination)"
    ),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[StockTransferResponse]:
    """List transfer records, optionally filtered by product or warehouse."""
    return await service.list(
        offset=offset,
        limit=limit,
        product_id=product_id,
        warehouse_id=warehouse_id,
    )


@router.get("/{transfer_id}", response_model=StockTransferResponse)
async def get_stock_transfer(
    transfer_id: int,
    service: ServiceDep,
) -> StockTransferResponse:
    """Retrieve a single transfer record by ID."""
    return await service.get(transfer_id)
