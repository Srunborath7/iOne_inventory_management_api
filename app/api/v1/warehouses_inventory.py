from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_account
from app.core.database import get_db
from app.domain.auth.model import Auth
from app.domain.warehouses_inventory.schema import (
    StockTransferRequest,
    StockTransferResponse,
    WarehousesInventoryCreate,
    WarehousesInventoryResponse,
    WarehousesInventoryUpdate,
)
from app.repositories.warehouses_inventory_repository import (
    WarehousesInventoryRepository,
)
from app.services.warehouses_inventory_service import WarehousesInventoryService

router = APIRouter(
    prefix="/warehouses-inventory",
    tags=["Warehouses Inventory"],
    dependencies=[Depends(get_current_account)],
)


def get_service(session: Annotated[AsyncSession, Depends(get_db)]) -> WarehousesInventoryService:
    return WarehousesInventoryService(WarehousesInventoryRepository(session))


ServiceDep = Annotated[WarehousesInventoryService, Depends(get_service)]


@router.post("", response_model=WarehousesInventoryResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse_inventory(
    payload: WarehousesInventoryCreate,
    service: ServiceDep,
    current_account: Annotated[Auth, Depends(get_current_account)],
) -> WarehousesInventoryResponse:
    return await service.create(payload, user_id=current_account.id)


@router.get("", response_model=list[WarehousesInventoryResponse])
async def list_warehouse_inventories(
    service: ServiceDep,
    product_id: int | None = Query(default=None, description="Filter by product ID"),
    warehouses_id: int | None = Query(default=None, description="Filter by warehouse ID"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[WarehousesInventoryResponse]:
    return await service.list(
        offset=offset,
        limit=limit,
        product_id=product_id,
        warehouses_id=warehouses_id,
    )


@router.get("/{inventory_id}", response_model=WarehousesInventoryResponse)
async def get_warehouse_inventory(
    inventory_id: int,
    service: ServiceDep,
) -> WarehousesInventoryResponse:
    return await service.get(inventory_id)


@router.put("/{inventory_id}", response_model=WarehousesInventoryResponse)
async def update_warehouse_inventory(
    inventory_id: int,
    payload: WarehousesInventoryUpdate,
    service: ServiceDep,
    current_account: Annotated[Auth, Depends(get_current_account)],
) -> WarehousesInventoryResponse:
    return await service.update(inventory_id, payload, user_id=current_account.id)


@router.post("/{inventory_id}/adjust-stock", response_model=WarehousesInventoryResponse)
async def adjust_warehouse_inventory_stock(
    inventory_id: int,
    delta: Annotated[int, Body(embed=True, description="Amount to add (positive) or deduct (negative)")],
    service: ServiceDep,
    current_account: Annotated[Auth, Depends(get_current_account)],
) -> WarehousesInventoryResponse:
    return await service.adjust_stock(inventory_id, delta=delta, user_id=current_account.id)


@router.post("/transfer", response_model=StockTransferResponse)
async def transfer_stock(
    payload: StockTransferRequest,
    service: ServiceDep,
    current_account: Annotated[Auth, Depends(get_current_account)],
) -> StockTransferResponse:
    src, dest = await service.transfer_stock(
        from_warehouse_id=payload.from_warehouse_id,
        to_warehouse_id=payload.to_warehouse_id,
        product_id=payload.product_id,
        quantity=payload.quantity,
        user_id=current_account.id,
    )
    return StockTransferResponse(
        source_inventory=WarehousesInventoryResponse.model_validate(src),
        destination_inventory=WarehousesInventoryResponse.model_validate(dest),
        transferred_quantity=payload.quantity,
    )


@router.delete("/{inventory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_warehouse_inventory(
    inventory_id: int,
    service: ServiceDep,
) -> None:
    await service.delete(inventory_id)
