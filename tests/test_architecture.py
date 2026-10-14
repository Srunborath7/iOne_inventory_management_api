import unittest
from unittest.mock import AsyncMock, MagicMock

from app.core.config import Settings
from app.core.exceptions import AppException, BadRequest, Conflict, NotFound, Unauthorized
from app.domain.activity_logs.model import ActivityLog
from app.domain.auth.model import Auth
from app.domain.brands.model import Brand
from app.domain.brands.schema import BrandCreate, BrandResponse, BrandRespone, BrandUpdate
from app.domain.categories.model import Category
from app.domain.categories.schema import CategoryCreate, CategoryResponse, CategoryRespone, CategoryUpdate
from app.domain.products.model import Product
from app.domain.suppliers.model import Supplier, Suppliers
from app.domain.suppliers.schema import SupplierCreate, SupplierResponse, SupplierUpdate
from app.domain.warehouses.model import Warehouse, Warehouses
from app.domain.warehouses.schema import WarehouseCreate, WarehouseResponse, WarehouseUpdate
from app.repositories import (
    ActivityLogRepository,
    AuthRepository,
    BaseRepository,
    BrandRepository,
    CategoryRepository,
    ProductRepository,
    SuppliersRepository,
    WarehousesRepository,
)
from app.services import (
    ActivityLogService,
    AuthService,
    BaseService,
    BrandService,
    CategoryService,
    ProductService,
    SuppliersService,
    WarehouseService,
)


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
        """Verify domain models follow SQLAlchemy OOP standards and table mappings."""
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

        # Product model checks
        self.assertEqual(Product.__tablename__, "products")
        product_cols = {c.name for c in Product.__table__.columns}
        self.assertTrue({"id", "name", "barcode", "created_by", "updated_by", "created_at", "updated_at"}.issubset(product_cols))

        # ActivityLog model checks
        self.assertEqual(ActivityLog.__tablename__, "activity_logs")
        log_cols = {c.name for c in ActivityLog.__table__.columns}
        self.assertTrue({"id", "user_id", "action", "entity_type", "entity_id", "description", "created_at"}.issubset(log_cols))

        # Suppliers model checks
        self.assertEqual(Suppliers.__tablename__, "suppliers")
        supp_cols = {c.name for c in Suppliers.__table__.columns}
        self.assertTrue({"id", "name", "contact", "phone", "address", "is_active", "created_at", "updated_at"}.issubset(supp_cols))
        self.assertIs(Supplier, Suppliers)

        # Warehouses model checks
        self.assertEqual(Warehouses.__tablename__, "warehouses")
        wh_cols = {c.name for c in Warehouses.__table__.columns}
        self.assertTrue({"id", "name", "code", "address", "is_active", "created_at", "updated_at"}.issubset(wh_cols))
        self.assertIs(Warehouse, Warehouses)

    def test_schema_aliases_and_typing(self):
        """Verify schema aliases and model instantiation."""
        self.assertIs(BrandRespone, BrandResponse)
        self.assertIs(CategoryRespone, CategoryResponse)

        # Brand schema instantiation
        create_data = BrandCreate(name="Apple", description="Tech brand")
        self.assertEqual(create_data.name, "Apple")

        update_data = BrandUpdate(name="Apple Inc.")
        self.assertEqual(update_data.name, "Apple Inc.")

        # Warehouse schema aliases
        wh_create = WarehouseCreate(name="Main Hub", code="WH-01", address="123 St")
        self.assertEqual(wh_create.name, "Main Hub")

        # Supplier schema aliases
        supp_create = SupplierCreate(name="Global Supplies", age=30, gender="male")
        self.assertEqual(supp_create.name, "Global Supplies")

    def test_repository_oop_instances(self):
        """Verify repositories properly inherit from BaseRepository and initialize with AsyncSession."""
        session_mock = MagicMock()

        brand_repo = BrandRepository(session_mock)
        self.assertIsInstance(brand_repo, BaseRepository)
        self.assertIs(brand_repo.session, session_mock)

        cat_repo = CategoryRepository(session_mock)
        self.assertIsInstance(cat_repo, BaseRepository)
        self.assertIs(cat_repo.session, session_mock)

        auth_repo = AuthRepository(session_mock)
        self.assertIsInstance(auth_repo, BaseRepository)
        self.assertIs(auth_repo.session, session_mock)

        product_repo = ProductRepository(session_mock)
        self.assertIsInstance(product_repo, BaseRepository)
        self.assertIs(product_repo.session, session_mock)

        log_repo = ActivityLogRepository(session_mock)
        self.assertIsInstance(log_repo, BaseRepository)
        self.assertIs(log_repo.session, session_mock)

        supp_repo = SuppliersRepository(session_mock)
        self.assertIsInstance(supp_repo, BaseRepository)
        self.assertIs(supp_repo.session, session_mock)

        wh_repo = WarehousesRepository(session_mock)
        self.assertIsInstance(wh_repo, BaseRepository)
        self.assertIs(wh_repo.session, session_mock)

    def test_service_oop_inheritance(self):
        """Verify services inherit from BaseService."""
        session_mock = MagicMock()
        brand_repo = BrandRepository(session_mock)
        cat_repo = CategoryRepository(session_mock)
        auth_repo = AuthRepository(session_mock)
        prod_repo = ProductRepository(session_mock)
        log_repo = ActivityLogRepository(session_mock)
        supp_repo = SuppliersRepository(session_mock)
        wh_repo = WarehousesRepository(session_mock)

        brand_service = BrandService(brand_repo)
        self.assertIsInstance(brand_service, BaseService)
        self.assertEqual(brand_service.UPLOAD_FOLDER, "brands")

        cat_service = CategoryService(cat_repo)
        self.assertIsInstance(cat_service, BaseService)
        self.assertEqual(cat_service.UPLOAD_FOLDER, "categories")

        prod_service = ProductService(prod_repo)
        self.assertIsInstance(prod_service, BaseService)
        self.assertEqual(prod_service.UPLOAD_FOLDER, "products")

        auth_service = AuthService(auth_repo)
        self.assertIsInstance(auth_service, BaseService)

        log_service = ActivityLogService(log_repo)
        self.assertIsInstance(log_service, BaseService)

        supp_service = SuppliersService(supp_repo)
        self.assertIsInstance(supp_service, BaseService)

        wh_service = WarehouseService(wh_repo)
        self.assertIsInstance(wh_service, BaseService)

    def test_exceptions_oop_hierarchy(self):
        """Verify exception hierarchy adheres to OOP principles."""
        self.assertTrue(issubclass(NotFound, AppException))
        self.assertTrue(issubclass(Conflict, AppException))
        self.assertTrue(BadRequest, AppException)
        self.assertTrue(issubclass(Unauthorized, AppException))

    async def test_brand_service_validation(self):
        """Verify validation in BrandService."""
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

    async def test_warehouse_service_validation(self):
        """Verify validation in WarehouseService."""
        mock_repo = MagicMock(spec=WarehousesRepository)
        mock_repo.get_by_name = AsyncMock(return_value=None)
        mock_repo.get_by_code = AsyncMock(return_value=None)
        service = WarehouseService(mock_repo)

        # Conflict validation on name
        mock_repo.get_by_name = AsyncMock(return_value=Warehouses(id=1, name="Central", code="W1", address="A"))
        with self.assertRaises(Conflict):
            await service.create(WarehouseCreate(name="Central", code="W2", address="B"))


if __name__ == "__main__":
    unittest.main()
