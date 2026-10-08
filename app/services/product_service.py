from decimal import Decimal
from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BadRequest, Conflict, NotFound
from app.core.upload import remove_image, save_image
from app.domain.products.model import Product
from app.domain.products.schema import ProductCreate, ProductUpdate
from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.product_repository import ProductRepository
from app.services.base import BaseService


class ProductService(BaseService[ProductRepository]):
    """
    Business Logic Layer for Products (OOP - Encapsulation & Separation of Concerns).
    Encapsulates product business rules, image management, stock rules, validation,
    and audit activity logging.
    """

    UPLOAD_FOLDER: str = "products"

    def __init__(self, repository: ProductRepository):
        super().__init__(repository)

    async def get(self, product_id: int) -> Product:
        """Fetch a product by ID or raise NotFound."""
        product = await self.repository.get(product_id)
        if product is None:
            raise NotFound("Product")
        return product

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[Product]:
        """Fetch a paginated list of products."""
        return await self.repository.list_all(offset=offset, limit=limit)

    async def create(
        self,
        data: ProductCreate,
        user_id: int,
        image: UploadFile | None = None,
    ) -> Product:
        """Create a new product with business validation, audit trail, and image handling."""
        name = data.name.strip()
        if not name:
            raise BadRequest("Product name cannot be empty")

        barcode = data.barcode.strip()
        if not barcode:
            raise BadRequest("Product barcode cannot be empty")

        if await self.repository.get_by_name(name):
            raise Conflict("Product name already exists")

        if await self.repository.get_by_barcode(barcode):
            raise Conflict("Product barcode already exists")

        stored_image = await save_image(image, self.UPLOAD_FOLDER)
        image_url = stored_image[0] if stored_image else data.image_url

        try:
            product = await self.repository.create(
                name=name,
                description=data.description,
                image_url=image_url,
                selling_price=data.selling_price,
                cost_price=data.cost_price,
                min_stock=data.min_stock,
                max_stock=data.max_stock,
                barcode=barcode,
                brand_id=data.brand_id,
                category_id=data.category_id,
                created_by=user_id,
                updated_by=user_id,
            )

            # Log product creation activity
            activity_repo = ActivityLogRepository(self.repository.session)
            await activity_repo.create(
                user_id=user_id,
                action="CREATE",
                entity_type="Product",
                entity_id=product.id,
                description=f"Created product '{product.name}' (barcode: {product.barcode})",
            )

            return product
        except IntegrityError as exc:
            if stored_image:
                await remove_image(image_url)
            raise Conflict("Product with this name or barcode already exists") from exc
        except Exception:
            if stored_image:
                await remove_image(image_url)
            raise

    async def update(
        self,
        product_id: int,
        data: ProductUpdate,
        user_id: int | None = None,
        image: UploadFile | None = None,
    ) -> Product:
        """Update an existing product, handling unique constraints, audit trail, and image replacement."""
        product = await self.get(product_id)
        changes = data.model_dump(exclude_unset=True)

        if "name" in changes and changes["name"] is not None:
            name = changes["name"].strip()
            if not name:
                raise BadRequest("Product name cannot be empty")
            existing = await self.repository.get_by_name(name)
            if existing and existing.id != product_id:
                raise Conflict("Product name already exists")
            changes["name"] = name

        if "barcode" in changes and changes["barcode"] is not None:
            barcode = changes["barcode"].strip()
            if not barcode:
                raise BadRequest("Product barcode cannot be empty")
            existing_bc = await self.repository.get_by_barcode(barcode)
            if existing_bc and existing_bc.id != product_id:
                raise Conflict("Product barcode already exists")
            changes["barcode"] = barcode

        if user_id is not None:
            changes["updated_by"] = user_id

        stored_image = await save_image(image, self.UPLOAD_FOLDER)
        old_image_url = product.image_url

        if stored_image:
            changes["image_url"] = stored_image[0]

        try:
            updated = await self.repository.update(product, changes)

            # Log product update activity
            if user_id is not None:
                activity_repo = ActivityLogRepository(self.repository.session)
                await activity_repo.create(
                    user_id=user_id,
                    action="UPDATE",
                    entity_type="Product",
                    entity_id=updated.id,
                    description=f"Updated product '{updated.name}'",
                )
        except IntegrityError as exc:
            if stored_image:
                await remove_image(stored_image[0])
            raise Conflict("Product conflict occurred") from exc
        except Exception:
            if stored_image:
                await remove_image(stored_image[0])
            raise

        if stored_image and old_image_url:
            await remove_image(old_image_url)

        return updated

    async def delete(self, product_id: int, user_id: int | None = None) -> None:
        """Delete a product, log the activity, and clean up its associated image file."""
        product = await self.get(product_id)
        image_url = product.image_url
        product_name = product.name

        await self.repository.delete(product)

        # Log product deletion activity
        if user_id is not None:
            activity_repo = ActivityLogRepository(self.repository.session)
            await activity_repo.create(
                user_id=user_id,
                action="DELETE",
                entity_type="Product",
                entity_id=product_id,
                description=f"Deleted product '{product_name}'",
            )

        if image_url:
            await remove_image(image_url)