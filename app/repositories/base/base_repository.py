from typing import Any, Generic, TypeVar
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic OOP Base Repository encapsulating common CRUD and session handling."""

    def __init__(self, session: AsyncSession, model: type[ModelType]):
        self.session = session
        self.model = model

    async def get(self, entity_id: Any) -> ModelType | None:
        """Fetch a single record by primary key."""
        return await self.session.get(self.model, entity_id)

    async def get_by_id(self, entity_id: Any) -> ModelType | None:
        """Alias for get(entity_id)."""
        return await self.get(entity_id)

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: Any = None,
    ) -> list[ModelType]:
        """Fetch a paginated list of records."""
        stmt = select(self.model)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        elif hasattr(self.model, "id"):
            stmt = stmt.order_by(getattr(self.model, "id"))
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **attrs: Any) -> ModelType:
        """Instantiate, persist, commit, and refresh an entity."""
        entity = self.model(**attrs)
        self.session.add(entity)
        await self._commit()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: ModelType, changes: dict[str, Any]) -> ModelType:
        """Apply dictionary changes to an entity, commit, and refresh."""
        for field, value in changes.items():
            setattr(entity, field, value)
        await self._commit()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: ModelType) -> None:
        """Delete an entity and commit."""
        await self.session.delete(entity)
        await self._commit()

    async def count(self) -> int:
        """Return the total number of records."""
        count_attr = getattr(self.model, "id", None)
        col = count_attr if count_attr is not None else 1
        stmt = select(func.count(col))
        result = await self.session.execute(stmt)
        return int(result.scalar_one_or_none() or 0)

    async def _commit(self) -> None:
        """Commit transaction with automatic rollback on failure."""
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        except Exception:
            await self.session.rollback()
            raise
