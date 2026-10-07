import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError

from app.domain.catgories.model import Category
from app.domain.catgories.schema import CategoryCreate, CategoryUpdate
from app.repositories.category_repository import CategoryRepository


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CATEGORY_IMAGE_DIR = PROJECT_ROOT / "uploads" / "categories"
MAX_IMAGE_SIZE = 5 * 1024 * 1024
IMAGE_FORMATS = (
    (b"\x89PNG\r\n\x1a\n", ".png", "image/png"),
    (b"\xff\xd8\xff", ".jpg", "image/jpeg"),
)


class CategoryNotFound(Exception):
    pass


class CategoryNameExists(Exception):
    pass


class InvalidCategoryImage(Exception):
    pass


class InvalidCategoryName(Exception):
    pass


async def save_category_image(upload: UploadFile | None) -> tuple[str, Path] | None:
    if upload is None or not upload.filename:
        return None

    content = await upload.read(MAX_IMAGE_SIZE + 1)
    if not content:
        raise InvalidCategoryImage("The uploaded image is empty.")
    if len(content) > MAX_IMAGE_SIZE:
        raise InvalidCategoryImage("Image must be 5 MB or smaller.")

    image_format = next(
        (fmt for fmt in IMAGE_FORMATS if content.startswith(fmt[0])),
        None,
    )
    if image_format is None and len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        image_format = (b"RIFF", ".webp", "image/webp")
    if image_format is None:
        raise InvalidCategoryImage("Upload a PNG, JPEG, or WebP image.")

    _, extension, _ = image_format
    filename = f"{uuid4().hex}{extension}"
    destination = CATEGORY_IMAGE_DIR / filename
    await asyncio.to_thread(CATEGORY_IMAGE_DIR.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread(destination.write_bytes, content)
    return f"/uploads/categories/{filename}", destination


async def remove_category_image(image_url: str | None) -> None:
    if not image_url:
        return
    file_path = CATEGORY_IMAGE_DIR / Path(image_url).name
    await asyncio.to_thread(file_path.unlink, missing_ok=True)


class CategoryService:
    def __init__(self, repository: CategoryRepository):
        self.repository = repository

    async def create(
        self,
        data: CategoryCreate,
        image: UploadFile | None = None,
    ) -> Category:
        name = data.name.strip()
        if not name:
            raise InvalidCategoryName
        if await self.repository.get_by_name(name):
            raise CategoryNameExists

        stored_image = await save_category_image(image)
        image_url = stored_image[0] if stored_image else None
        try:
            return await self.repository.create(
                name=name,
                description=data.description,
                image_url=image_url,
            )
        except IntegrityError as exc:
            if stored_image:
                await remove_category_image(image_url)
            raise CategoryNameExists from exc
        except Exception:
            if stored_image:
                await remove_category_image(image_url)
            raise

    async def get(self, category_id: int) -> Category:
        category = await self.repository.get(category_id)
        if category is None:
            raise CategoryNotFound
        return category

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[Category]:
        return await self.repository.list(offset=offset, limit=limit)

    async def update(
        self,
        category_id: int,
        data: CategoryUpdate,
        image: UploadFile | None = None,
    ) -> Category:
        category = await self.get(category_id)
        changes = data.model_dump(exclude_unset=True)
        if "name" in changes:
            name = (changes["name"] or "").strip()
            if not name:
                raise InvalidCategoryName
            existing = await self.repository.get_by_name(name)
            if existing and existing.id != category_id:
                raise CategoryNameExists
            changes["name"] = name

        stored_image = await save_category_image(image)
        old_image_url = category.image_url
        if stored_image:
            changes["image_url"] = stored_image[0]
        try:
            updated = await self.repository.update(category, changes)
        except IntegrityError as exc:
            if stored_image:
                await remove_category_image(stored_image[0])
            raise CategoryNameExists from exc
        except Exception:
            if stored_image:
                await remove_category_image(stored_image[0])
            raise

        if stored_image and old_image_url:
            await remove_category_image(old_image_url)
        return updated

    async def delete(self, category_id: int) -> None:
        category = await self.get(category_id)
        image_url = category.image_url
        await self.repository.delete(category)
        if image_url:
            await remove_category_image(image_url)
