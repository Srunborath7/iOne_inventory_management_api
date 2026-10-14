from alembic import op
import sqlalchemy as sa


revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_transfers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("from_warehouse_id", sa.Integer(), nullable=False),
        sa.Column("to_warehouse_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["from_warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["to_warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["auth_accounts.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index("ix_stock_transfers_product_id", "stock_transfers", ["product_id"])
    op.create_index(
        "ix_stock_transfers_from_warehouse_id", "stock_transfers", ["from_warehouse_id"]
    )
    op.create_index(
        "ix_stock_transfers_to_warehouse_id", "stock_transfers", ["to_warehouse_id"]
    )
    op.create_index("ix_stock_transfers_created_by", "stock_transfers", ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_stock_transfers_created_by", table_name="stock_transfers")
    op.drop_index("ix_stock_transfers_to_warehouse_id", table_name="stock_transfers")
    op.drop_index("ix_stock_transfers_from_warehouse_id", table_name="stock_transfers")
    op.drop_index("ix_stock_transfers_product_id", table_name="stock_transfers")
    op.drop_table("stock_transfers")
