"""Add destination warehouse to purchase orders."""

from alembic import op
import sqlalchemy as sa


revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "purchase_orders",
        sa.Column("warehouse_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_purchase_orders_warehouse_id_warehouses",
        "purchase_orders",
        "warehouses",
        ["warehouse_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_purchase_orders_warehouse_id", "purchase_orders", ["warehouse_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_purchase_orders_warehouse_id", table_name="purchase_orders")
    op.drop_constraint(
        "fk_purchase_orders_warehouse_id_warehouses",
        "purchase_orders",
        type_="foreignkey",
    )
    op.drop_column("purchase_orders", "warehouse_id")
