from alembic import op
import sqlalchemy as sa


revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        # Primary key
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        # Basic information
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=255), nullable=True),
        # Pricing
        sa.Column("selling_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("cost_price", sa.Numeric(10, 2), nullable=False),
        # Stock thresholds
        sa.Column("min_stock", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("max_stock", sa.Integer(), server_default=sa.text("0"), nullable=False),
        # Product identification
        sa.Column("barcode", sa.String(length=100), nullable=False),
        # Relationships
        sa.Column("brand_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        # Status
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("barcode", name="uq_products_barcode"),
        sa.UniqueConstraint("name", name="uq_products_name"),
    )
    # Indexes
    op.create_index("ix_products_brand_id", "products", ["brand_id"])
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index("ix_products_barcode", "products", ["barcode"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_products_barcode", table_name="products")
    op.drop_index("ix_products_category_id", table_name="products")
    op.drop_index("ix_products_brand_id", table_name="products")
    op.drop_table("products")