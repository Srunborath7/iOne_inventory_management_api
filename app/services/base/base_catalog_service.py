from typing import Any, Generic, TypeVar
from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError

from app.core.database import Base
from app.core.exceptions import BadRequest, Conflict, NotFound
from app.core.upload import remove_image, save_image
from app.repositories.base import BaseRepository
from app.services.base.base_service import BaseService

ModelType = TypeVar("ModelType", bound=Base)
RepoType = TypeVar("RepoType", bound=BaseRepository)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseCatalogService(
    BaseService[RepoType],
    Generic[ModelType, RepoType, CreateSchemaType, UpdateSchemaType],
):
    """
    Generic catalog service providing OOP business logic for catalog entities
    such as Categories and Brands with automated image handling and validation.
    """

    entity_name: str = "Resource"
    upload_folder: str = "catalog"

    def __init__(self, repository: RepoType):
        super().__init__(repository)

    async def get(self, entity_id: int) -> ModelType:
        """Retrieve an entity by ID or raise NotFound."""
        entity = await self.repository.get(entity_id)
        if entity is None:
            raise NotFound(self.entity_name)
        return entity

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[ModelType]:
        """List entities with pagination."""
        return await self.repository.list(offset=offset, limit=limit)

    async def create(
        self,
        data: CreateSchemaType,
        image: UploadFile | None = None,
    ) -> ModelType:
        """Create a new catalog item with image upload and conflict prevention."""
        raw_name = getattr(data, "name", "")
        name = raw_name.strip() if raw_name else ""
        if not name:
            raise BadRequest(f"{self.entity_name} name cannot be empty")

        if await self.repository.get_by_name(name):
            raise Conflict(f"{self.entity_name} name already exists")

        description = getattr(data, "description", None)
        stored_image = await save_image(image, self.upload_folder)
        image_url = stored_image[0] if stored_image else None

        try:
            return await self.repository.create(
                name=name,
                description=description,
                image_url=image_url,
            )
        except IntegrityError as exc:
            if stored_image:
                await remove_image(image_url)
            raise Conflict(f"{self.entity_name} name already exists") from exc
        except Exception:
            if stored_image:
                await remove_image(image_url)
            raise

    async def update(
        self,
        entity_id: int,
        data: UpdateSchemaType,
        image: UploadFile | None = None,
    ) -> ModelType:
        """Update an existing catalog item, managing image replacement and conflicts."""
        entity = await self.get(entity_id)

        if hasattr(data, "model_dump"):
            changes = data.model_dump(exclude_unset=True)
        elif isinstance(data, dict):
            changes = dict(data)
        else:
            changes = {}

        if "name" in changes:
            raw_name = changes.get("name")
            name = (raw_name or "").strip()
            if not name:
                raise BadRequest(f"{self.entity_name} name cannot be empty")
            existing = await self.repository.get_by_name(name)
            if existing and getattr(existing, "id") != entity_id:
                raise Conflict(f"{self.entity_name} name already exists")
            changes["name"] = name

        stored_image = await save_image(image, self.upload_folder)
        old_image_url = getattr(entity, "image_url", None)

        if stored_image:
            changes["image_url"] = stored_image[0]

        try:
            updated = await self.repository.update(entity, changes)
        except IntegrityError as exc:
            if stored_image:
                await remove_image(stored_image[0])
            raise Conflict(f"{self.entity_name} name already exists") from exc
        except Exception:
            if stored_image:
                await remove_image(stored_image[0])
            raise

        if stored_image and old_image_url:
            await remove_image(old_image_url)

        return updated

    async def delete(self, entity_id: int) -> None:
        """Delete a catalog item and cleans up its associated image file."""
        entity = await self.get(entity_id)
        image_url = getattr(entity, "image_url", None)
        await self.repository.delete(entity)
        if image_url:
            await remove_image(image_url)
