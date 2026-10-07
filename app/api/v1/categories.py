from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_account
from app.core.database import get_db
from app.domain.catgories.schema import CategoryCreate, CategoryResponse, CategoryUpdate
from app.repositories.category_repository import CategoryRepository
from app.services.category_service import (
    CategoryNameExists,
    CategoryNotFound,
    CategoryService,
    InvalidCategoryImage,
    InvalidCategoryName,
)


router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    dependencies=[Depends(get_current_account)],
)


def get_service(session: AsyncSession) -> CategoryService:
    return CategoryService(CategoryRepository(session))


def handle_category_error(exc: Exception) -> HTTPException:
    if isinstance(exc, CategoryNotFound):
        return HTTPException(status_code=404, detail="Category not found.")
    if isinstance(exc, CategoryNameExists):
        return HTTPException(status_code=409, detail="Category name already exists.")
    if isinstance(exc, InvalidCategoryImage):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=422, detail="Category name cannot be empty.")


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    name: Annotated[str, Form(min_length=1, max_length=100)],
    description: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
    session: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    service = get_service(session)
    try:
        return await service.create(CategoryCreate(name=name, description=description), image)
    except (CategoryNameExists, InvalidCategoryImage, InvalidCategoryName) as exc:
        raise handle_category_error(exc) from None


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
) -> list[CategoryResponse]:
    return await get_service(session).list(offset=offset, limit=limit)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    session: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    try:
        return await get_service(session).get(category_id)
    except CategoryNotFound:
        raise handle_category_error(CategoryNotFound()) from None


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    name: Annotated[str | None, Form(min_length=1, max_length=100)] = None,
    description: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
    session: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    values: dict[str, str | None] = {}
    if name is not None:
        values["name"] = name
    if description is not None:
        values["description"] = description or None
    service = get_service(session)
    try:
        return await service.update(category_id, CategoryUpdate(**values), image)
    except (CategoryNotFound, CategoryNameExists, InvalidCategoryImage, InvalidCategoryName) as exc:
        raise handle_category_error(exc) from None


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    session: AsyncSession = Depends(get_db),
) -> Response:
    try:
        await get_service(session).delete(category_id)
    except CategoryNotFound:
        raise handle_category_error(CategoryNotFound()) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
