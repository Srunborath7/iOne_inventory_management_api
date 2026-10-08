from app.domain.brands.model import Brand
from app.domain.brands.schema import BrandCreate, BrandUpdate
from app.repositories.brand_repository import BrandRepository
from app.services.base import BaseCatalogService


class BrandService(
    BaseCatalogService[Brand, BrandRepository, BrandCreate, BrandUpdate]
):
    """Business logic service for Brands."""

    entity_name = "Brand"
    upload_folder = "brands"

    def __init__(self, repository: BrandRepository):
        super().__init__(repository)
