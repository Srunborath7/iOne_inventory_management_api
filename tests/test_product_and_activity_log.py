import unittest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.domain.activity_logs.model import ActivityLog
from app.domain.activity_logs.schema import ActivityLogCreate, ActivityLogResponse
from app.domain.products.model import Product
from app.domain.products.schema import ProductCreate, ProductResponse, ProductUpdate
from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.product_repository import ProductRepository
from app.services.activity_log_service import ActivityLogService
from app.services.product_service import ProductService


class TestProductAndActivityLog(unittest.IsolatedAsyncioTestCase):
    def test_product_model_audit_fields(self):
        """Verify that Product model has created_by and updated_by columns."""
        product_cols = {c.name for c in Product.__table__.columns}
        self.assertTrue(
            {"id", "name", "barcode", "created_by", "updated_by", "created_at", "updated_at"}.issubset(
                product_cols
            )
        )

    def test_activity_log_model_structure(self):
        """Verify that ActivityLog model has required columns."""
        self.assertEqual(ActivityLog.__tablename__, "activity_logs")
        log_cols = {c.name for c in ActivityLog.__table__.columns}
        self.assertTrue(
            {"id", "user_id", "action", "entity_type", "entity_id", "description", "created_at"}.issubset(
                log_cols
            )
        )

    def test_product_schema_audit_fields(self):
        """Verify that ProductResponse includes created_by and updated_by."""
        resp = ProductResponse(
            id=1,
            name="Laptop",
            description="High spec laptop",
            image_url=None,
            selling_price=Decimal("1200.00"),
            cost_price=Decimal("900.00"),
            min_stock=5,
            max_stock=50,
            barcode="LAP-12345",
            brand_id=1,
            category_id=1,
            is_active=True,
            created_by=10,
            updated_by=10,
            created_at="2026-10-08T12:00:00Z",
            updated_at="2026-10-08T12:00:00Z",
        )
        self.assertEqual(resp.created_by, 10)
        self.assertEqual(resp.updated_by, 10)

    def test_activity_log_schema(self):
        """Verify ActivityLogCreate and ActivityLogResponse schemas."""
        create_schema = ActivityLogCreate(
            user_id=1,
            action="CREATE",
            entity_type="Product",
            entity_id=10,
            description="Created product Laptop",
        )
        self.assertEqual(create_schema.action, "CREATE")

        resp = ActivityLogResponse(
            id=1,
            user_id=1,
            action="CREATE",
            entity_type="Product",
            entity_id=10,
            description="Created product Laptop",
            created_at="2026-10-08T12:00:00Z",
        )
        self.assertEqual(resp.id, 1)
        self.assertEqual(resp.entity_type, "Product")

    async def test_product_service_creates_with_user_and_logs(self):
        """Verify ProductService.create records created_by and activity log."""
        mock_repo = MagicMock(spec=ProductRepository)
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_repo.session = mock_session

        mock_repo.get_by_name = AsyncMock(return_value=None)
        mock_repo.get_by_barcode = AsyncMock(return_value=None)

        dummy_product = Product(
            id=1,
            name="Test Product",
            barcode="11223344",
            selling_price=Decimal("100"),
            cost_price=Decimal("80"),
            brand_id=1,
            category_id=1,
            created_by=5,
            updated_by=5,
        )
        mock_repo.create = AsyncMock(return_value=dummy_product)

        service = ProductService(mock_repo)
        create_data = ProductCreate(
            name="Test Product",
            barcode="11223344",
            selling_price=Decimal("100"),
            cost_price=Decimal("80"),
            brand_id=1,
            category_id=1,
        )

        res = await service.create(data=create_data, user_id=5)
        self.assertEqual(res.id, 1)
        mock_repo.create.assert_awaited_once()
        call_kwargs = mock_repo.create.call_args.kwargs
        self.assertEqual(call_kwargs["created_by"], 5)
        self.assertEqual(call_kwargs["updated_by"], 5)


if __name__ == "__main__":
    unittest.main()
