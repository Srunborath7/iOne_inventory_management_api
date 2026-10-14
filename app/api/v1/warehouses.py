from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_account
from app.core.database import get_db
from app.domain.warehouses.schema import (
    WarehousesCreate,
    WarehousesResponse,
    WarehousesUpdate,
)
from app.repositories.warehouses_repository import WarehousesRepository
from app.services.warehouses_service import WarehouseService

router = APIRouter(
    prefix="/warehouses",
    tags=["Warehouses"],
    dependencies=[Depends(get_current_account)],
)


def get_service(session: Annotated[AsyncSession, Depends(get_db)]) -> WarehouseService:
    return WarehouseService(WarehousesRepository(session))


ServiceDep = Annotated[WarehouseService, Depends(get_service)]


@router.post("", response_model=WarehousesResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    payload: WarehousesCreate,
    service: ServiceDep,
) -> WarehousesResponse:
    return await service.create(payload)


@router.get("", response_model=list[WarehousesResponse])
async def list_warehouses(
    service: ServiceDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[WarehousesResponse]:
    return await service.list(offset=offset, limit=limit)


@router.get("/{warehouse_id}", response_model=WarehousesResponse)
async def get_warehouse(warehouse_id: int, service: ServiceDep) -> WarehousesResponse:
    return await service.get(warehouse_id)


@router.put("/{warehouse_id}", response_model=WarehousesResponse)
async def update_warehouse(
    warehouse_id: int,
    payload: WarehousesUpdate,
    service: ServiceDep,
) -> WarehousesResponse:
    return await service.update(warehouse_id, payload)


@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_warehouse(warehouse_id: int, service: ServiceDep) -> None:
    await service.delete(warehouse_id)
