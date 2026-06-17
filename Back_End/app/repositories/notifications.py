from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import NotificationType
from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, notification: Notification) -> Notification:
        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)
        return notification

    async def get_by_id(self, notification_id: UUID, include_deleted: bool = False) -> Notification | None:
        statement = select(Notification).where(Notification.id == notification_id)
        if not include_deleted:
            statement = statement.where(Notification.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def list_all(self) -> list[Notification]:
        result = await self.session.scalars(
            select(Notification)
            .where(Notification.deleted_at.is_(None))
            .order_by(Notification.is_read, Notification.created_at.desc())
        )
        return list(result.all())

    async def unread_count(self) -> int:
        count = await self.session.scalar(
            select(func.count(Notification.id)).where(
                Notification.is_read.is_(False),
                Notification.deleted_at.is_(None),
            )
        )
        return int(count or 0)

    async def get_duplicate_unread(
        self,
        notification_type: NotificationType,
        class_id: UUID | None,
        target_user_id: UUID | None = None,
        target_student_id: UUID | None = None,
        target_teacher_id: UUID | None = None,
    ) -> Notification | None:
        return await self.session.scalar(
            select(Notification).where(
                Notification.type == notification_type,
                Notification.class_id == class_id,
                Notification.target_user_id == target_user_id,
                Notification.target_student_id == target_student_id,
                Notification.target_teacher_id == target_teacher_id,
                Notification.is_read.is_(False),
                Notification.deleted_at.is_(None),
            )
        )

    async def list_unread(self) -> list[Notification]:
        result = await self.session.scalars(
            select(Notification)
            .where(Notification.is_read.is_(False), Notification.deleted_at.is_(None))
            .order_by(Notification.created_at.desc())
        )
        return list(result.all())
