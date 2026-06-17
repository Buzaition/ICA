from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.responses import success_response
from app.db.session import get_session
from app.models.user import User
from app.schemas.notifications import NotificationProgressCheckRead, NotificationRead, NotificationUnreadCountRead
from app.services.notifications import NotificationService

router = APIRouter()


@router.get("/notifications")
async def list_notifications(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    notifications = await NotificationService(session).list_notifications(current_user)
    return success_response(data=[NotificationRead.from_model(item).model_dump(mode="json") for item in notifications])


@router.get("/notifications/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    count = await NotificationService(session).unread_count(current_user)
    return success_response(data=NotificationUnreadCountRead(unread_count=count).model_dump(mode="json"))


@router.post("/notifications/check-progress")
async def check_progress_notifications(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    notifications = await NotificationService(session).check_progress(current_user)
    data = NotificationProgressCheckRead(
        created_count=len(notifications),
        notifications=[NotificationRead.from_model(item) for item in notifications],
    )
    return success_response(data=data.model_dump(mode="json"))


@router.post("/notifications/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    notification = await NotificationService(session).mark_read(notification_id, current_user)
    return success_response(data=NotificationRead.from_model(notification).model_dump(mode="json"))


@router.post("/notifications/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    notifications = await NotificationService(session).mark_all_read(current_user)
    return success_response(data=[NotificationRead.from_model(item).model_dump(mode="json") for item in notifications])
