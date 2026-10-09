from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.auth import get_current_account
from app.core.database import get_db
from app.domain.suppliers.schema import SuppliersCreate, SuppliersResponse, SuppliersUpdate
from app.repositories.suppliers_repository import SuppliersRepository
from app.services.suppliers_service import SuppliersService

router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
    dependencies=[Depends(get_current_account)],
)

def get_service(session: Annotated[AsyncSession, Depends(get_db)]) -> SuppliersService:
    return SuppliersService(SuppliersRepository(session))


ServiceDep = Annotated[SuppliersService, Depends(get_service)]

@router.get("", response_model=list[SuppliersResponse])
async def list_categories(
    service: ServiceDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[SuppliersResponse]:
    return await service.list(offset=offset, limit=limit)

@router.post("", response_model=SuppliersResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    payload: SuppliersCreate,
    service: ServiceDep,
) -> SuppliersResponse:
    return await service.create(payload)

@router.put("/{supplier_id}", response_model=SuppliersResponse)
async def update_supplier(
    supplier_id: int,
    payload: SuppliersUpdate,
    service: ServiceDep,
) -> SuppliersResponse:
    return await service.update(supplier_id, payload)

@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(supplier_id: int, service: ServiceDep) -> None:
    await service.delete(supplier_id)
