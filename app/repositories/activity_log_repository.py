from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.activity_logs.model import ActivityLog
from app.repositories.base import BaseRepository


class ActivityLogRepository(BaseRepository[ActivityLog]):
    """Repository handling database operations for ActivityLog audit trail (OOP - Inheritance)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ActivityLog)

    async def get(self, log_id: int) -> ActivityLog | None:
        """Fetch an activity log by ID with user relation pre-loaded."""
        result = await self._session.execute(
            select(ActivityLog)
            .options(joinedload(ActivityLog.user))
            .where(ActivityLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        user_id: int | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ActivityLog]:
        """Fetch activity logs with optional filters and user relation pre-loaded."""
        query = select(ActivityLog).options(joinedload(ActivityLog.user))

        if user_id is not None:
            query = query.where(ActivityLog.user_id == user_id)
        if action is not None:
            query = query.where(ActivityLog.action == action.upper())
        if entity_type is not None:
            query = query.where(ActivityLog.entity_type == entity_type)
        if entity_id is not None:
            query = query.where(ActivityLog.entity_id == entity_id)

        query = (
            query.order_by(desc(ActivityLog.created_at), desc(ActivityLog.id))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(query)
        return list(result.scalars().unique().all())

    async def create(
        self,
        *,
        user_id: int | None = None,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        description: str | None = None,
    ) -> ActivityLog:
        """Create and persist an activity log record."""
        return await super().create(
            user_id=user_id,
            action=action.upper(),
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
        )
