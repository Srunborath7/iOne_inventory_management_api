import unittest
from unittest.mock import AsyncMock, MagicMock

from app.core.config import Settings
from app.core.exceptions import AppException, BadRequest, Conflict, NotFound, Unauthorized
from app.domain.auth.model import Auth
from app.domain.brands.model import Brand
from app.domain.brands.schema import BrandCreate, BrandResponse, BrandRespone, BrandUpdate
from app.domain.categories.model import Category
from app.domain.categories.schema import CategoryCreate, CategoryResponse, CategoryRespone, CategoryUpdate
from app.repositories import AuthRepository, BaseRepository, BrandRepository, CategoryRepository
from app.services import AuthService, BaseCatalogService, BaseService, BrandService, CategoryService


class TestOOPArchitecture(unittest.IsolatedAsyncioTestCase):
    def test_settings_render_database_url_normalization(self):
        """Verify that Render postgres:// and postgresql:// URLs convert to postgresql+asyncpg://"""
        render_url_1 = "postgres://user:pass@dpg-xxx.oregon-postgres.render.com/mydb"
        converted_1 = Settings.assemble_database_url(render_url_1)
        self.assertEqual(converted_1, "postgresql+asyncpg://user:pass@dpg-xxx.oregon-postgres.render.com/mydb")

        render_url_2 = "postgresql://user:pass@dpg-xxx.oregon-postgres.render.com/mydb"
        converted_2 = Settings.assemble_database_url(render_url_2)
        self.assertEqual(converted_2, "postgresql+asyncpg://user:pass@dpg-xxx.oregon-postgres.render.com/mydb")

        already_async = "postgresql+asyncpg://user:pass@localhost:5432/mydb"
        converted_3 = Settings.assemble_database_url(already_async)
        self.assertEqual(converted_3, already_async)

    def test_domain_model_oop_structure(self):
        """Verify Brand, Category, and Auth models follow SQLAlchemy OOP standards."""
        # Brand model checks
        self.assertEqual(Brand.__tablename__, "brands")
        brand_cols = {c.name for c in Brand.__table__.columns}
        self.assertTrue({"id", "name", "description", "image_url", "created_at", "updated_at"}.issubset(brand_cols))

        # Category model checks
        self.assertEqual(Category.__tablename__, "categories")
        cat_cols = {c.name for c in Category.__table__.columns}
        self.assertTrue({"id", "name", "description", "image_url", "created_at", "updated_at"}.issubset(cat_cols))

        # Auth model checks
        self.assertEqual(Auth.__tablename__, "auth_accounts")
        auth_cols = {c.name for c in Auth.__table__.columns}
        self.assertTrue({"id", "full_name", "email", "password_hash", "created_at"}.issubset(auth_cols))

    def test_schema_aliases_and_typing(self):
        """Verify BrandRespone and BrandResponse compatibility."""
        self.assertIs(BrandRespone, BrandResponse)
        self.assertIs(CategoryRespone, CategoryResponse)

        # Brand schema instantiation
        create_data = BrandCreate(name="Apple", description="Tech brand")
        self.assertEqual(create_data.name, "Apple")

        update_data = BrandUpdate(name="Apple Inc.")
        self.assertEqual(update_data.name, "Apple Inc.")

    def test_repository_oop_inheritance(self):
        """Verify repositories properly inherit from BaseRepository."""
        session_mock = MagicMock()

        brand_repo = BrandRepository(session_mock)
        self.assertIsInstance(brand_repo, BaseRepository)
        self.assertIs(brand_repo.model, Brand)
        self.assertIs(brand_repo.session, session_mock)

        cat_repo = CategoryRepository(session_mock)
        self.assertIsInstance(cat_repo, BaseRepository)
        self.assertIs(cat_repo.model, Category)

        auth_repo = AuthRepository(session_mock)
        self.assertIsInstance(auth_repo, BaseRepository)
        self.assertIs(auth_repo.model, Auth)

    def test_service_oop_inheritance(self):
        """Verify services inherit from BaseCatalogService and BaseService."""
        session_mock = MagicMock()
        brand_repo = BrandRepository(session_mock)
        cat_repo = CategoryRepository(session_mock)
        auth_repo = AuthRepository(session_mock)

        brand_service = BrandService(brand_repo)
        self.assertIsInstance(brand_service, BaseCatalogService)
        self.assertIsInstance(brand_service, BaseService)
        self.assertEqual(brand_service.entity_name, "Brand")
        self.assertEqual(brand_service.upload_folder, "brands")

        cat_service = CategoryService(cat_repo)
        self.assertIsInstance(cat_service, BaseCatalogService)
        self.assertEqual(cat_service.entity_name, "Category")
        self.assertEqual(cat_service.upload_folder, "categories")

        auth_service = AuthService(auth_repo)
        self.assertIsInstance(auth_service, BaseService)

    def test_exceptions_oop_hierarchy(self):
        """Verify exception hierarchy adheres to OOP principles."""
        self.assertTrue(issubclass(NotFound, AppException))
        self.assertTrue(issubclass(Conflict, AppException))
        self.assertTrue(issubclass(BadRequest, AppException))
        self.assertTrue(issubclass(Unauthorized, AppException))

    async def test_base_catalog_service_validation(self):
        """Verify validation in BaseCatalogService."""
        mock_repo = MagicMock(spec=BrandRepository)
        mock_repo.get_by_name = AsyncMock(return_value=None)
        service = BrandService(mock_repo)

        # Empty name validation
        with self.assertRaises(BadRequest):
            await service.create(BrandCreate(name="   ", description=None))

        # Conflict validation
        mock_repo.get_by_name = AsyncMock(return_value=Brand(id=1, name="Sony"))
        with self.assertRaises(Conflict):
            await service.create(BrandCreate(name="Sony", description="Electronics"))


if __name__ == "__main__":
    unittest.main()
