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
from app.domain.catgories.schema import CategoryCreate, CategoryResponse, CategoryUpdate
from app.repositories.category_repository import CategoryRepository
from app.services.category_service import CategoryService


router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    dependencies=[Depends(get_current_account)],
)


def get_service(session: Annotated[AsyncSession, Depends(get_db)]) -> CategoryService:
    return CategoryService(CategoryRepository(session))


ServiceDep = Annotated[CategoryService, Depends(get_service)]


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    service: ServiceDep,
    name: Annotated[str, Form(min_length=1, max_length=100)],
    description: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
) -> CategoryResponse:
    return await service.create(CategoryCreate(name=name, description=description), image)


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    service: ServiceDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[CategoryResponse]:
    return await service.list(offset=offset, limit=limit)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, service: ServiceDep) -> CategoryResponse:
    return await service.get(category_id)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    service: ServiceDep,
    name: Annotated[str | None, Form(min_length=1, max_length=100)] = None,
    description: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
) -> CategoryResponse:
    values: dict[str, str | None] = {}
    if name is not None:
        values["name"] = name
    if description is not None:
        values["description"] = description or None
    return await service.update(category_id, CategoryUpdate(**values), image)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, service: ServiceDep) -> None:
    await service.delete(category_id)