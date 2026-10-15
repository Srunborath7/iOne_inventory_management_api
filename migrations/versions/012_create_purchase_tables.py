"""Create purchase order and supplier return tables."""

from alembic import op
import sqlalchemy as sa


revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_number", sa.String(length=50), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("ordered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_number", name="uq_purchase_orders_order_number"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["auth_accounts.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_purchase_orders_supplier_id", "purchase_orders", ["supplier_id"])
    op.create_index("ix_purchase_orders_created_by", "purchase_orders", ["created_by"])

    op.create_table(
        "purchase_order_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("ordered_quantity", sa.Integer(), nullable=False),
        sa.Column("received_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("unit_cost", sa.Numeric(10, 2), nullable=False),
        sa.CheckConstraint("ordered_quantity > 0", name="ck_purchase_order_items_ordered_positive"),
        sa.CheckConstraint("received_quantity >= 0", name="ck_purchase_order_items_received_nonnegative"),
        sa.CheckConstraint("received_quantity <= ordered_quantity", name="ck_purchase_order_items_received_lte_ordered"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_purchase_order_items_unit_cost_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_purchase_order_items_purchase_order_id", "purchase_order_items", ["purchase_order_id"])
    op.create_index("ix_purchase_order_items_product_id", "purchase_order_items", ["product_id"])

    op.create_table(
        "purchase_returns",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("return_number", sa.String(length=50), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=True),
        sa.Column("returned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("return_number", name="uq_purchase_returns_return_number"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["auth_accounts.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_purchase_returns_supplier_id", "purchase_returns", ["supplier_id"])
    op.create_index("ix_purchase_returns_purchase_order_id", "purchase_returns", ["purchase_order_id"])
    op.create_index("ix_purchase_returns_created_by", "purchase_returns", ["created_by"])

    op.create_table(
        "purchase_return_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("purchase_return_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_cost", sa.Numeric(10, 2), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_purchase_return_items_quantity_positive"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_purchase_return_items_unit_cost_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["purchase_return_id"], ["purchase_returns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_purchase_return_items_purchase_return_id", "purchase_return_items", ["purchase_return_id"])
    op.create_index("ix_purchase_return_items_product_id", "purchase_return_items", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_purchase_return_items_product_id", table_name="purchase_return_items")
    op.drop_index("ix_purchase_return_items_purchase_return_id", table_name="purchase_return_items")
    op.drop_table("purchase_return_items")
    op.drop_index("ix_purchase_returns_created_by", table_name="purchase_returns")
    op.drop_index("ix_purchase_returns_purchase_order_id", table_name="purchase_returns")
    op.drop_index("ix_purchase_returns_supplier_id", table_name="purchase_returns")
    op.drop_table("purchase_returns")
    op.drop_index("ix_purchase_order_items_product_id", table_name="purchase_order_items")
    op.drop_index("ix_purchase_order_items_purchase_order_id", table_name="purchase_order_items")
    op.drop_table("purchase_order_items")
    op.drop_index("ix_purchase_orders_created_by", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_supplier_id", table_name="purchase_orders")
    op.drop_table("purchase_orders")
