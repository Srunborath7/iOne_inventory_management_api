from alembic import op
import sqlalchemy as sa


revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "warehouse_inventory",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("warehouses_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["warehouses_id"], ["warehouses.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["auth_accounts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"], ["auth_accounts.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "product_id", "warehouses_id", name="uq_inventory_product_warehouse"
        ),
        sa.CheckConstraint("quantity >= 0", name="ck_inventory_quantity_non_negative"),
    )
    op.create_index(
        "ix_warehouse_inventory_product_id", "warehouse_inventory", ["product_id"]
    )
    op.create_index(
        "ix_warehouse_inventory_warehouses_id", "warehouse_inventory", ["warehouses_id"]
    )
    op.create_index(
        "ix_warehouse_inventory_created_by", "warehouse_inventory", ["created_by"]
    )
    op.create_index(
        "ix_warehouse_inventory_updated_by", "warehouse_inventory", ["updated_by"]
    )


def downgrade() -> None:
    op.drop_index("ix_warehouse_inventory_updated_by", table_name="warehouse_inventory")
    op.drop_index("ix_warehouse_inventory_created_by", table_name="warehouse_inventory")
    op.drop_index("ix_warehouse_inventory_warehouses_id", table_name="warehouse_inventory")
    op.drop_index("ix_warehouse_inventory_product_id", table_name="warehouse_inventory")
    op.drop_table("warehouse_inventory")