from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_account
from app.core.database import get_db
from app.domain.brands.schema import BrandCreate, BrandResponse, BrandUpdate
from app.repositories.brand_repository import BrandRepository
from app.services.brand_service import BrandService

router = APIRouter(
    prefix="/brands",
    tags=["Brands"],
    dependencies=[Depends(get_current_account)],
)


def get_service(session: Annotated[AsyncSession, Depends(get_db)]) -> BrandService:
    return BrandService(BrandRepository(session))


ServiceDep = Annotated[BrandService, Depends(get_service)]


@router.post("", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    service: ServiceDep,
    name: Annotated[str, Form(min_length=1, max_length=100)],
    description: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
) -> BrandResponse:
    return await service.create(BrandCreate(name=name, description=description), image)


@router.get("", response_model=list[BrandResponse])
async def list_brands(
    service: ServiceDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[BrandResponse]:
    return await service.list(offset=offset, limit=limit)


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(brand_id: int, service: ServiceDep) -> BrandResponse:
    return await service.get(brand_id)


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: int,
    service: ServiceDep,
    name: Annotated[str | None, Form(min_length=1, max_length=100)] = None,
    description: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
) -> BrandResponse:
    values: dict[str, str | None] = {}
    if name is not None:
        values["name"] = name
    if description is not None:
        values["description"] = description or None
    return await service.update(brand_id, BrandUpdate(**values), image)


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(brand_id: int, service: ServiceDep) -> None:
    await service.delete(brand_id)
