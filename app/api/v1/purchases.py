from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_account
from app.core.database import get_db
from app.domain.auth.model import Auth
from app.domain.purchase.schema import (
    PurchaseOrderCreate,
    PurchaseOrderReceive,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    PurchaseReturnCreate,
    PurchaseReturnResponse,
    PurchaseReturnUpdate,
)
from app.repositories.purchase_repository import PurchaseRepository
from app.services.purchase_service import PurchaseService

router = APIRouter(
    prefix="/purchases",
    tags=["Purchases"],
    dependencies=[Depends(get_current_account)],
)


def get_service(session: Annotated[AsyncSession, Depends(get_db)]) -> PurchaseService:
    return PurchaseService(PurchaseRepository(session))


ServiceDep = Annotated[PurchaseService, Depends(get_service)]


@router.post(
    "/orders", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED
)
async def create_purchase_order(
    payload: PurchaseOrderCreate,
    service: ServiceDep,
    current_account: Annotated[Auth, Depends(get_current_account)],
) -> PurchaseOrderResponse:
    return await service.create_order(payload, user_id=current_account.id)


@router.get("/orders", response_model=list[PurchaseOrderResponse])
async def list_purchase_orders(
    service: ServiceDep,
    supplier_id: int | None = Query(default=None, gt=0),
    order_status: str | None = Query(default=None, alias="status", max_length=20),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[PurchaseOrderResponse]:
    return await service.list_orders(
        supplier_id=supplier_id, status=order_status, offset=offset, limit=limit
    )


@router.get("/orders/{order_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(order_id: int, service: ServiceDep) -> PurchaseOrderResponse:
    return await service.get_order(order_id)


@router.patch("/orders/{order_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    order_id: int,
    payload: PurchaseOrderUpdate,
    service: ServiceDep,
) -> PurchaseOrderResponse:
    """Edit a draft purchase order and optionally replace its lines."""
    return await service.update_order(order_id, payload)


@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase_order(order_id: int, service: ServiceDep) -> None:
    """Delete a draft purchase order."""
    await service.delete_order(order_id)


@router.post("/orders/{order_id}/ready", response_model=PurchaseOrderResponse)
async def mark_purchase_order_ready(
    order_id: int, service: ServiceDep
) -> PurchaseOrderResponse:
    """Mark a draft order as ready to receive at its destination warehouse."""
    return await service.mark_order_ready(order_id)


@router.post("/orders/{order_id}/receive", response_model=PurchaseOrderResponse)
async def receive_purchase_order(
    order_id: int,
    payload: PurchaseOrderReceive,
    service: ServiceDep,
    current_account: Annotated[Auth, Depends(get_current_account)],
) -> PurchaseOrderResponse:
    """Receive order item quantities and add them to the selected warehouse."""
    quantities = {item.item_id: item.quantity for item in payload.items}
    return await service.receive_order(
        order_id, quantities, user_id=current_account.id
    )


@router.post(
    "/returns", response_model=PurchaseReturnResponse, status_code=status.HTTP_201_CREATED
)
async def create_purchase_return(
    payload: PurchaseReturnCreate,
    service: ServiceDep,
    current_account: Annotated[Auth, Depends(get_current_account)],
) -> PurchaseReturnResponse:
    return await service.create_return(payload, user_id=current_account.id)


@router.get("/returns", response_model=list[PurchaseReturnResponse])
async def list_purchase_returns(
    service: ServiceDep,
    supplier_id: int | None = Query(default=None, gt=0),
    purchase_order_id: int | None = Query(default=None, gt=0),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[PurchaseReturnResponse]:
    return await service.list_returns(
        supplier_id=supplier_id,
        purchase_order_id=purchase_order_id,
        offset=offset,
        limit=limit,
    )


@router.get("/returns/{return_id}", response_model=PurchaseReturnResponse)
async def get_purchase_return(return_id: int, service: ServiceDep) -> PurchaseReturnResponse:
    return await service.get_return(return_id)


@router.patch("/returns/{return_id}", response_model=PurchaseReturnResponse)
async def update_purchase_return(
    return_id: int,
    payload: PurchaseReturnUpdate,
    service: ServiceDep,
    current_account: Annotated[Auth, Depends(get_current_account)],
) -> PurchaseReturnResponse:
    return await service.update_return(
        return_id, payload, user_id=current_account.id
    )


@router.delete("/returns/{return_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase_return(
    return_id: int,
    service: ServiceDep,
    current_account: Annotated[Auth, Depends(get_current_account)],
) -> None:
    await service.delete_return(return_id, user_id=current_account.id)
