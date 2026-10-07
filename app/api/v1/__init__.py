from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.brand import router as brand_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(categories_router)
router.include_router(brand_router)
