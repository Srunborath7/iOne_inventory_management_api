from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, TypeVar
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

T = TypeVar("T")
ModelType = TypeVar("ModelType", bound=Base)


# ==============================================================================
# 1. Abstract Interface (Abstraction)
# ==============================================================================
class IRepository(ABC, Generic[T]):
    """
    Abstract Interface for Generic Repository Pattern.
    Defines the contract for all data access operations (OOP - Abstraction).
    """

    @abstractmethod
    async def get(self, item_id: int) -> Optional[T]:
        """Retrieve an item by its primary key ID."""
        pass

    @abstractmethod
    async def list_all(self, *, offset: int = 0, limit: int = 100) -> List[T]:
        """Retrieve a paginated list of items."""
        pass

    @abstractmethod
    async def create(self, **attrs: Any) -> T:
        """Create and persist a new item."""
        pass

    @abstractmethod
    async def update(self, item: T, changes: dict[str, Any]) -> T:
        """Update an existing item with changes dictionary."""
        pass

    @abstractmethod
    async def delete(self, item: T) -> None:
        """Delete an item."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Count the total number of items."""
        pass


# ==============================================================================
# 2. Database Implementation with SQLAlchemy (Encapsulation & Inheritance)
# ==============================================================================
class BaseRepository(IRepository[ModelType]):
    """
    SQLAlchemy Async implementation of IRepository.
    Encapsulates database sessions, transactions, and common CRUD queries.
    """

    def __init__(self, session: AsyncSession, model: type[ModelType]):
        self._session = session
        self._model = model

    @property
    def session(self) -> AsyncSession:
        """Protected access to the database session (Encapsulation)."""
        return self._session

    @property
    def model(self) -> type[ModelType]:
        """Protected access to the model class (Encapsulation)."""
        return self._model

    async def get(self, item_id: int) -> Optional[ModelType]:
        """Fetch a single record by primary key."""
        return await self._session.get(self._model, item_id)

    async def list_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: Any = None,
    ) -> List[ModelType]:
        """Fetch a paginated list of records."""
        stmt = select(self._model)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        elif hasattr(self._model, "id"):
            stmt = stmt.order_by(getattr(self._model, "id"))
        stmt = stmt.offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # Alias for backward compatibility with list()
    async def list(self, *, offset: int = 0, limit: int = 100) -> List[ModelType]:
        return await self.list_all(offset=offset, limit=limit)

    async def create(self, **attrs: Any) -> ModelType:
        """Instantiate, persist, commit, and refresh an entity."""
        entity = self._model(**attrs)
        self._session.add(entity)
        await self._commit()
        await self._session.refresh(entity)
        return entity

    async def update(self, item: ModelType, changes: dict[str, Any]) -> ModelType:
        """Apply dictionary changes to an entity, commit, and refresh."""
        for field, value in changes.items():
            setattr(item, field, value)
        await self._commit()
        await self._session.refresh(item)
        return item

    async def delete(self, item: ModelType) -> None:
        """Delete an entity from the database and commit."""
        await self._session.delete(item)
        await self._commit()

    async def count(self) -> int:
        """Return the total number of records."""
        count_attr = getattr(self._model, "id", None)
        col = count_attr if count_attr is not None else 1
        stmt = select(func.count(col))
        result = await self._session.execute(stmt)
        return int(result.scalar_one_or_none() or 0)

    async def _commit(self) -> None:
        """Internal helper to commit transaction with automatic rollback on failure."""
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise
        except Exception:
            await self._session.rollback()
            raise


# ==============================================================================
# 3. In-Memory Implementation (Polymorphism / Testing)
# ==============================================================================
class InMemoryRepository(IRepository[T]):
    """
    In-Memory implementation of IRepository.
    Useful for unit tests and illustrating OOP Polymorphism.
    """

    def __init__(self):
        self._items: dict[int, T] = {}
        self._counter: int = 1

    async def get(self, item_id: int) -> Optional[T]:
        return self._items.get(item_id)

    async def list_all(self, *, offset: int = 0, limit: int = 100) -> List[T]:
        all_items = list(self._items.values())
        return all_items[offset : offset + limit]

    async def create(self, **attrs: Any) -> T:
        item_id = self._counter
        self._counter += 1
        attrs["id"] = item_id
        # Assuming T is a class or dict-like object
        item = attrs  # type: ignore
        self._items[item_id] = item
        return item

    async def update(self, item: T, changes: dict[str, Any]) -> T:
        item_id = getattr(item, "id", None)
        if item_id and item_id in self._items:
            for key, val in changes.items():
                setattr(item, key, val)
            self._items[item_id] = item
        return item

    async def delete(self, item: T) -> None:
        item_id = getattr(item, "id", None)
        if item_id and item_id in self._items:
            del self._items[item_id]

    async def count(self) -> int:
        return len(self._items)
