from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_account
from app.core.database import get_db
from app.domain.auth.model import Auth
from app.domain.stock_movements.schema import StockMovementCreate, StockMovementResponse
from app.repositories.stock_movement_repository import StockMovementRepository
from app.repositories.warehouses_inventory_repository import WarehousesInventoryRepository
from app.services.stock_movement_service import StockMovementService

router = APIRouter(
    prefix="/stock-movements", tags=["Stock Movements"],
    dependencies=[Depends(get_current_account)],
)


def get_service(session: Annotated[AsyncSession, Depends(get_db)]) -> StockMovementService:
    return StockMovementService(
        StockMovementRepository(session), WarehousesInventoryRepository(session)
    )


ServiceDep = Annotated[StockMovementService, Depends(get_service)]


@router.post("", response_model=StockMovementResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_movement(
    payload: StockMovementCreate,
    service: ServiceDep,
    current_account: Annotated[Auth, Depends(get_current_account)],
) -> StockMovementResponse:
    return await service.create(payload, user_id=current_account.id)


@router.get("", response_model=list[StockMovementResponse])
async def list_stock_movements(
    service: ServiceDep,
    product_id: int | None = Query(default=None, gt=0),
    warehouse_id: int | None = Query(default=None, gt=0),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[StockMovementResponse]:
    return await service.list(
        product_id=product_id, warehouse_id=warehouse_id, offset=offset, limit=limit
    )


@router.get("/{movement_id}", response_model=StockMovementResponse)
async def get_stock_movement(movement_id: int, service: ServiceDep) -> StockMovementResponse:
    return await service.get(movement_id)
