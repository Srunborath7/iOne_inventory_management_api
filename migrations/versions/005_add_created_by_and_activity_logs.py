from alembic import op
import sqlalchemy as sa


revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add created_by and updated_by to products table if not already present
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("products")]

    if "created_by" not in columns:
        op.add_column(
            "products",
            sa.Column("created_by", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            "fk_products_created_by_auth_accounts",
            "products",
            "auth_accounts",
            ["created_by"],
            ["id"],
            ondelete="RESTRICT",
        )
        op.create_index("ix_products_created_by", "products", ["created_by"])

    if "updated_by" not in columns:
        op.add_column(
            "products",
            sa.Column("updated_by", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            "fk_products_updated_by_auth_accounts",
            "products",
            "auth_accounts",
            ["updated_by"],
            ["id"],
            ondelete="RESTRICT",
        )
        op.create_index("ix_products_updated_by", "products", ["updated_by"])

    # 2. Create activity_logs table
    if not inspector.has_table("activity_logs"):
        op.create_table(
            "activity_logs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("action", sa.String(length=50), nullable=False),
            sa.Column("entity_type", sa.String(length=50), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["auth_accounts.id"],
                ondelete="SET NULL",
            ),
        )
        op.create_index("ix_activity_logs_user_id", "activity_logs", ["user_id"])
        op.create_index("ix_activity_logs_action", "activity_logs", ["action"])
        op.create_index("ix_activity_logs_entity_type", "activity_logs", ["entity_type"])
        op.create_index("ix_activity_logs_entity_id", "activity_logs", ["entity_id"])


def downgrade() -> None:
    op.drop_index("ix_activity_logs_entity_id", table_name="activity_logs")
    op.drop_index("ix_activity_logs_entity_type", table_name="activity_logs")
    op.drop_index("ix_activity_logs_action", table_name="activity_logs")
    op.drop_index("ix_activity_logs_user_id", table_name="activity_logs")
    op.drop_table("activity_logs")

    op.drop_constraint("fk_products_updated_by_auth_accounts", "products", type_="foreignkey")
    op.drop_index("ix_products_updated_by", table_name="products")
    op.drop_column("products", "updated_by")

    op.drop_constraint("fk_products_created_by_auth_accounts", "products", type_="foreignkey")
    op.drop_index("ix_products_created_by", table_name="products")
    op.drop_column("products", "created_by")
