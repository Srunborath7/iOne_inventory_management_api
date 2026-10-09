import asyncio
import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.database_url,
    connect_args=settings.database_connect_args,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_recycle=300,
)


SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def import_all_models() -> None:
    """Import all domain models so they are registered with Base.metadata."""
    import app.domain.auth.model  # noqa: F401
    import app.domain.categories.model  # noqa: F401
    import app.domain.brands.model  # noqa: F401
    import app.domain.products.model  # noqa: F401
    import app.domain.activity_logs.model  # noqa: F401
    import app.domain.suppliers.model  # noqa: F401


async def init_db():
    # Ensure all domain models are imported and attached to Base.metadata
    import_all_models()

    # Use Alembic as the single schema-management mechanism when enabled.
    if not settings.auto_migrate:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("Database tables created/verified successfully via Base.metadata.create_all")
        except Exception as exc:
            logger.exception(
                "Base.metadata.create_all failed (%s): %r",
                type(exc).__name__,
                exc,
            )
        return

    from alembic import command
    from alembic.config import Config

    project_root = Path(__file__).resolve().parents[2]

    def upgrade_database() -> None:
        alembic_config = Config(str(project_root / "alembic.ini"))
        command.upgrade(alembic_config, "head")

    max_retries = 4
    for attempt in range(1, max_retries + 1):
        try:
            await asyncio.to_thread(upgrade_database)
            print("Database migrations applied successfully")
            return
        except Exception as exc:
            logger.exception(
                "Database migration failed on attempt %s/%s (%s): %r",
                attempt,
                max_retries,
                type(exc).__name__,
                exc,
            )
            if attempt < max_retries:
                await asyncio.sleep(2)


async def close_db():
    await engine.dispose()
    print("Database connection closed")


async def get_db():
    async with SessionLocal() as session:
        yield session


async def ping_db() -> bool:
    """Perform a lightweight database connectivity check for healthz endpoint."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
