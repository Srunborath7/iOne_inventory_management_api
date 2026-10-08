from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.activity_logs.model import ActivityLog


class ActivityLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, log_id: int) -> ActivityLog | None:
        result = await self.session.execute(
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
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        *,
        user_id: int | None = None,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        description: str | None = None,
    ) -> ActivityLog:
        log = ActivityLog(
            user_id=user_id,
            action=action.upper(),
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
        )
        self.session.add(log)
        await self._commit()
        await self.session.refresh(log)
        return log

    async def _commit(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
