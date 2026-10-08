from __future__ import annotations

from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BadRequest, Conflict, NotFound
from app.core.upload import remove_image, save_image
from app.domain.categories.model import Category
from app.domain.categories.schema import CategoryCreate, CategoryUpdate
from app.repositories.category_repository import CategoryRepository
from app.services.base import BaseService


class CategoryService(BaseService[CategoryRepository]):
    """
    Business Logic Layer for Categories (OOP - Encapsulation & Separation of Concerns).
    Encapsulates category business rules, image management, and validation.
    """

    UPLOAD_FOLDER: str = "categories"

    def __init__(self, repository: CategoryRepository):
        # Dependency Injection (OOP - Inversion of Control)
        super().__init__(repository)

    async def get(self, category_id: int) -> Category:
        """Fetch a category by ID or raise NotFound."""
        category = await self.repository.get(category_id)
        if category is None:
            raise NotFound("Category")
        return category

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[Category]:
        """Fetch a paginated list of categories."""
        return await self.repository.list_all(offset=offset, limit=limit)

    async def create(
        self,
        data: CategoryCreate,
        image: UploadFile | None = None,
    ) -> Category:
        """
        Create a new category with business validation and image handling.
        """
        name = data.name.strip()
        if not name:
            raise BadRequest("Category name cannot be empty")

        # Business Rule: Category names must be unique
        if await self.repository.get_by_name(name):
            raise Conflict("Category name already exists")

        # Handle optional image upload
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
            raise Conflict("Category name already exists") from exc
        except Exception:
            if stored_image:
                await remove_image(image_url)
            raise

    async def update(
        self,
        category_id: int,
        data: CategoryUpdate,
        image: UploadFile | None = None,
    ) -> Category:
        """
        Update an existing category, handling name uniqueness and image replacement.
        """
        category = await self.get(category_id)
        changes = data.model_dump(exclude_unset=True)

        # Validate unique name if updated
        if "name" in changes:
            name = (changes.get("name") or "").strip()
            if not name:
                raise BadRequest("Category name cannot be empty")
            existing = await self.repository.get_by_name(name)
            if existing and existing.id != category_id:
                raise Conflict("Category name already exists")
            changes["name"] = name

        # Handle image replacement
        stored_image = await save_image(image, self.UPLOAD_FOLDER)
        old_image_url = category.image_url

        if stored_image:
            changes["image_url"] = stored_image[0]

        try:
            updated = await self.repository.update(category, changes)
        except IntegrityError as exc:
            if stored_image:
                await remove_image(stored_image[0])
            raise Conflict("Category name already exists") from exc
        except Exception:
            if stored_image:
                await remove_image(stored_image[0])
            raise

        # Clean up old image after successful DB update
        if stored_image and old_image_url:
            await remove_image(old_image_url)

        return updated

    async def delete(self, category_id: int) -> None:
        """Delete a category and remove its associated image file."""
        category = await self.get(category_id)
        image_url = category.image_url

        await self.repository.delete(category)

        if image_url:
            await remove_image(image_url)