from __future__ import annotations

from app.core.exceptions import NotFound
from app.domain.activity_logs.model import ActivityLog
from app.domain.activity_logs.schema import ActivityLogCreate
from app.repositories.activity_log_repository import ActivityLogRepository
from app.services.base import BaseService


class ActivityLogService(BaseService[ActivityLogRepository]):
    def __init__(self, repository: ActivityLogRepository):
        super().__init__(repository)

    async def get(self, log_id: int) -> ActivityLog:
        log = await self.repository.get(log_id)
        if log is None:
            raise NotFound("ActivityLog")
        return log

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
        return await self.repository.list(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            offset=offset,
            limit=limit,
        )

    async def log(
        self,
        data: ActivityLogCreate,
    ) -> ActivityLog:
        return await self.repository.create(
            user_id=data.user_id,
            action=data.action,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            description=data.description,
        )
