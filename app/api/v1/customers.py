from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_account
from app.core.database import get_db
from app.domain.customers.schema import (
    CustomersCreate,
    CustomersResponse,
    CustomersUpdate,
)
from app.repositories.customers_repository import CustomersRepository
from app.services.customers_service import CustomersService

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
    dependencies=[Depends(get_current_account)],
)

def get_service(session: Annotated[AsyncSession, Depends(get_db)]) -> CustomersService:
    return CustomersService(CustomersRepository(session))


ServiceDep = Annotated[CustomersService, Depends(get_service)]


@router.post("", response_model=CustomersResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomersCreate,
    service: ServiceDep,
) -> CustomersResponse:
    return await service.create(payload)


@router.get("", response_model=list[CustomersResponse])
async def list_customers(
    service: ServiceDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[CustomersResponse]:
    return await service.list(offset=offset, limit=limit)


@router.get("/{customer_id}", response_model=CustomersResponse)
async def get_customer(
    customer_id: int,
    service: ServiceDep,
) -> CustomersResponse:
    return await service.get(customer_id)


@router.put("/{customer_id}", response_model=CustomersResponse)
async def update_customer(
    customer_id: int,
    payload: CustomersUpdate,
    service: ServiceDep,
) -> CustomersResponse:
    return await service.update(customer_id, payload)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(customer_id: int, service: ServiceDep) -> None:
    await service.delete(customer_id)
