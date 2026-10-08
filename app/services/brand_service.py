from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BadRequest, Conflict, NotFound
from app.core.upload import remove_image, save_image
from app.domain.brands.model import Brand
from app.domain.brands.schema import BrandCreate, BrandUpdate
from app.repositories.brand_repository import BrandRepository
from app.services.base import BaseService


class BrandService(BaseService[BrandRepository]):
    """
    Business Logic Layer for Brands (OOP - Encapsulation & Separation of Concerns).
    Encapsulates brand business rules, image management, and validation.
    """

    UPLOAD_FOLDER: str = "brands"

    def __init__(self, repository: BrandRepository):
        super().__init__(repository)

    async def get(self, brand_id: int) -> Brand:
        """Fetch a brand by ID or raise NotFound."""
        brand = await self.repository.get(brand_id)
        if brand is None:
            raise NotFound("Brand")
        return brand

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[Brand]:
        """Fetch a paginated list of brands."""
        return await self.repository.list_all(offset=offset, limit=limit)

    async def create(
        self,
        data: BrandCreate,
        image: UploadFile | None = None,
    ) -> Brand:
        """Create a new brand with validation and image handling."""
        name = data.name.strip()
        if not name:
            raise BadRequest("Brand name cannot be empty")

        if await self.repository.get_by_name(name):
            raise Conflict("Brand name already exists")

        stored_image = await save_image(image, self.UPLOAD_FOLDER)
        image_url = stored_image[0] if stored_image else None

        try:
            return await self.repository.create(
                name=name,
                description=data.description,
                image_url=image_url,
            )
        except IntegrityError as exc:
            if stored_image:
                await remove_image(image_url)
            raise Conflict("Brand name already exists") from exc
        except Exception:
            if stored_image:
                await remove_image(image_url)
            raise

    async def update(
        self,
        brand_id: int,
        data: BrandUpdate,
        image: UploadFile | None = None,
    ) -> Brand:
        """Update an existing brand."""
        brand = await self.get(brand_id)
        changes = data.model_dump(exclude_unset=True)

        if "name" in changes:
            name = (changes.get("name") or "").strip()
            if not name:
                raise BadRequest("Brand name cannot be empty")
            existing = await self.repository.get_by_name(name)
            if existing and existing.id != brand_id:
                raise Conflict("Brand name already exists")
            changes["name"] = name

        stored_image = await save_image(image, self.UPLOAD_FOLDER)
        old_image_url = brand.image_url

        if stored_image:
            changes["image_url"] = stored_image[0]

        try:
            updated = await self.repository.update(brand, changes)
        except IntegrityError as exc:
            if stored_image:
                await remove_image(stored_image[0])
            raise Conflict("Brand name already exists") from exc
        except Exception:
            if stored_image:
                await remove_image(stored_image[0])
            raise

        if stored_image and old_image_url:
            await remove_image(old_image_url)

        return updated

    async def delete(self, brand_id: int) -> None:
        """Delete a brand and its associated image file."""
        brand = await self.get(brand_id)
        image_url = brand.image_url

        await self.repository.delete(brand)

        if image_url:
            await remove_image(image_url)
