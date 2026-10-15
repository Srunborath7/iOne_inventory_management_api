"""Apply Alembic migrations, adopting the known pre-Alembic base schema."""

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings


BASE_REVISION_TABLES = {
    "auth_accounts",
    "categories",
    "brands",
    "products",
    "activity_logs",
    "suppliers",
}
LATER_REVISION_TABLES = {
    "warehouses",
    "warehouse_inventory",
    "stock_transfers",
    "stock_movements",
    "customers",
}


async def public_tables() -> set[str]:
    engine = create_async_engine(
        settings.database_url,
        connect_args=settings.database_connect_args,
        pool_pre_ping=True,
    )
    try:
        async with engine.connect() as connection:
            return await connection.run_sync(
                lambda sync_connection: set(
                    inspect(sync_connection).get_table_names(schema="public")
                )
            )
    finally:
        await engine.dispose()


def main() -> None:
    tables = asyncio.run(public_tables())
    base_tables = tables & BASE_REVISION_TABLES
    later_tables = tables & LATER_REVISION_TABLES

    project_root = Path(__file__).resolve().parents[2]
    config = Config(str(project_root / "alembic.ini"))

    if "alembic_version" not in tables and base_tables:
        if base_tables != BASE_REVISION_TABLES or later_tables:
            raise RuntimeError(
                "Database has an untracked partial schema. Expected all tables "
                "from revisions 001-006 and none from 007-011 before adopting "
                f"revision 006. Found base tables: {sorted(base_tables)}; "
                f"later tables: {sorted(later_tables)}. Resolve the schema "
                "before running migrations."
            )
        print("Existing 001-006 schema found; recording Alembic revision 006.")
        command.stamp(config, "006")

    command.upgrade(config, "head")
    print("Database migrations are up to date.")


if __name__ == "__main__":
    main()
