from app.domain.categories.model import Category
from app.domain.categories.schema import CategoryCreate, CategoryUpdate
from app.repositories.category_repository import CategoryRepository
from app.services.base import BaseCatalogService


class CategoryService(
    BaseCatalogService[Category, CategoryRepository, CategoryCreate, CategoryUpdate]
):
    """Business logic service for Categories."""

    entity_name = "Category"
    upload_folder = "categories"

    def __init__(self, repository: CategoryRepository):
        super().__init__(repository)