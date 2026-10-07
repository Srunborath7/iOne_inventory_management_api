from pathlib import Path
from app.repositories.brand_repository import BrandRepository
from app.domain.brands.model import Brand
from app.domain.brands.schema import BrandCreate
from app.core.exceptions import NotFound, BadRequest, Conflict
from app.core.upload import UploadFile, save_image, remove_image
from sqlalchemy.exc import IntegrityError

class BrandService:
    def __init__(self, repository: BrandRepository):
        self.repository = repository

    async def get(self, brand_id: int) -> Brand:
        brand = await self.repository.get(brand_id)
        if not brand:
            raise NotFound("Brands")
        return brand

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[Brand]:
        return await self.repository.list(offset=offset, limit=limit)

    async def create(self, data: BrandCreate, image: UploadFile | None) -> Brand:
        name = data.name.strip()
        if not name:
            raise BadRequest("Brand name cannot be empty")
        if await self.repository.get_by_name(name):
            raise Conflict("Brand name already exists")

        store_image = await save_image(image, "brands")
        image_url = store_image[0] if store_image else None

        try:
            return await self.repository.create(
                name=name,
                description=data.description,
                image_url=image_url,
            )
        except IntegrityError as exc:
            if store_image:
                await remove_image(image_url)
                raise Conflict("Category name already exists") from exc
        except Exception:
            if store_image:
                await remove_image(image_url)
                raise
