from fastapi import APIRouter, Depends, Query, status, Form, File
from app.api.v1.auth import get_current_account
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.brand_service import BrandService
from app.repositories.brand_repository import BrandRepository
from app.domain.brands.schema import BrandRespone, BrandCreate
from app.core.upload import UploadFile

router = APIRouter(prefix="/brands", tags=["Brands"], dependencies= [Depends(get_current_account)])

def get_service(session: Annotated[AsyncSession, Depends(get_db)]) -> BrandService:
    return BrandService(BrandRepository(session))

serviceDep = Annotated[BrandService, Depends(get_service)]

@router.get("", response_model=list[BrandRespone])
async def list_brand(
    service: serviceDep, 
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100)) -> list[BrandRespone]:

    return await service.list(offset=offset, limit=limit)

@router.post("", response_model=BrandRespone, status_code=status.HTTP_201_CREATED)
async def create_brand(
    service: serviceDep,
    name: Annotated[str, Form(min_length=1, max_length=100)],
    description: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
) -> BrandRespone:
    return await service.create(BrandCreate(name=name, description=description), image)
