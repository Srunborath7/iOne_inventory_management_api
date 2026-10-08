from decimal import Decimal
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
from app.domain.products.schema import ProductCreate, ProductResponse, ProductUpdate
from app.repositories.product_repository import ProductRepository
from app.services.product_service import ProductService

router = APIRouter(
    prefix="/products",
    tags=["Products"],
    dependencies=[Depends(get_current_account)],
)


def get_service(session: Annotated[AsyncSession, Depends(get_db)]) -> ProductService:
    return ProductService(ProductRepository(session))


ServiceDep = Annotated[ProductService, Depends(get_service)]


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    service: ServiceDep,
    name: Annotated[str, Form(min_length=1, max_length=150)],
    selling_price: Annotated[Decimal, Form(gt=0)],
    cost_price: Annotated[Decimal, Form(gt=0)],
    barcode: Annotated[str, Form(min_length=1, max_length=100)],
    brand_id: Annotated[int, Form()],
    category_id: Annotated[int, Form()],
    description: Annotated[str | None, Form()] = None,
    min_stock: Annotated[int, Form(ge=0)] = 0,
    max_stock: Annotated[int, Form(ge=0)] = 0,
    image: Annotated[UploadFile | None, File()] = None,
) -> ProductResponse:
    data = ProductCreate(
        name=name,
        description=description,
        selling_price=selling_price,
        cost_price=cost_price,
        min_stock=min_stock,
        max_stock=max_stock,
        barcode=barcode,
        brand_id=brand_id,
        category_id=category_id,
    )
    return await service.create(data, image)


@router.get("", response_model=list[ProductResponse])
async def list_products(
    service: ServiceDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[ProductResponse]:
    return await service.list(offset=offset, limit=limit)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, service: ServiceDep) -> ProductResponse:
    return await service.get(product_id)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    service: ServiceDep,
    name: Annotated[str | None, Form(min_length=1, max_length=150)] = None,
    description: Annotated[str | None, Form()] = None,
    selling_price: Annotated[Decimal | None, Form(gt=0)] = None,
    cost_price: Annotated[Decimal | None, Form(gt=0)] = None,
    min_stock: Annotated[int | None, Form(ge=0)] = None,
    max_stock: Annotated[int | None, Form(ge=0)] = None,
    barcode: Annotated[str | None, Form(min_length=1, max_length=100)] = None,
    brand_id: Annotated[int | None, Form()] = None,
    category_id: Annotated[int | None, Form()] = None,
    is_active: Annotated[bool | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
) -> ProductResponse:
    values: dict = {}
    if name is not None:
        values["name"] = name
    if description is not None:
        values["description"] = description
    if selling_price is not None:
        values["selling_price"] = selling_price
    if cost_price is not None:
        values["cost_price"] = cost_price
    if min_stock is not None:
        values["min_stock"] = min_stock
    if max_stock is not None:
        values["max_stock"] = max_stock
    if barcode is not None:
        values["barcode"] = barcode
    if brand_id is not None:
        values["brand_id"] = brand_id
    if category_id is not None:
        values["category_id"] = category_id
    if is_active is not None:
        values["is_active"] = is_active

    return await service.update(product_id, ProductUpdate(**values), image)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, service: ServiceDep) -> None:
    await service.delete(product_id)