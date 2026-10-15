"""Track returned quantities against purchase order lines."""

from alembic import op
import sqlalchemy as sa


revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "purchase_order_items",
        sa.Column("returned_quantity", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_check_constraint(
        "ck_purchase_order_items_returned_nonnegative",
        "purchase_order_items",
        "returned_quantity >= 0",
    )
    op.create_check_constraint(
        "ck_purchase_order_items_returned_lte_received",
        "purchase_order_items",
        "returned_quantity <= received_quantity",
    )
    op.add_column(
        "purchase_return_items",
        sa.Column("purchase_order_item_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_purchase_return_items_order_item",
        "purchase_return_items",
        "purchase_order_items",
        ["purchase_order_item_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_purchase_return_items_purchase_order_item_id",
        "purchase_return_items",
        ["purchase_order_item_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_purchase_return_items_purchase_order_item_id",
        table_name="purchase_return_items",
    )
    op.drop_constraint(
        "fk_purchase_return_items_order_item",
        "purchase_return_items",
        type_="foreignkey",
    )
    op.drop_column("purchase_return_items", "purchase_order_item_id")
    op.drop_constraint(
        "ck_purchase_order_items_returned_lte_received",
        "purchase_order_items",
        type_="check",
    )
    op.drop_constraint(
        "ck_purchase_order_items_returned_nonnegative",
        "purchase_order_items",
        type_="check",
    )
    op.drop_column("purchase_order_items", "returned_quantity")
