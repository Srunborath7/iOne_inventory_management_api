import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.database_url,
    echo=True,
)


SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    from alembic import command
    from alembic.config import Config

    project_root = Path(__file__).resolve().parents[2]

    def upgrade_database() -> None:
        alembic_config = Config(str(project_root / "alembic.ini"))
        command.upgrade(alembic_config, "head")

    await asyncio.to_thread(upgrade_database)
    print("Database migrations applied")


async def close_db():
    await engine.dispose()
    print("Database connection closed")


async def get_db():
    async with SessionLocal() as session:
        yield session
