from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_account
from app.core.database import get_db
from app.domain.activity_logs.schema import ActivityLogResponse
from app.domain.auth.model import Auth
from app.repositories.activity_log_repository import ActivityLogRepository
from app.services.activity_log_service import ActivityLogService

router = APIRouter(
    prefix="/activity-logs",
    tags=["Activity Logs"],
    dependencies=[Depends(get_current_account)],
)


def get_service(session: Annotated[AsyncSession, Depends(get_db)]) -> ActivityLogService:
    return ActivityLogService(ActivityLogRepository(session))


ServiceDep = Annotated[ActivityLogService, Depends(get_service)]


@router.get("", response_model=list[ActivityLogResponse])
async def list_activity_logs(
    service: ServiceDep,
    user_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: int | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[ActivityLogResponse]:
    return await service.list(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        offset=offset,
        limit=limit,
    )


@router.get("/{log_id}", response_model=ActivityLogResponse)
async def get_activity_log(log_id: int, service: ServiceDep) -> ActivityLogResponse:
    return await service.get(log_id)
