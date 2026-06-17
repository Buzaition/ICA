from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.enums import NotificationSeverity, NotificationType
from app.models.notification import Notification


class NotificationRead(BaseModel):
    id: UUID
    type: NotificationType
    title: str
    message: str
    target_user_id: UUID | None
    target_student_id: UUID | None
    target_teacher_id: UUID | None
    class_id: UUID | None
    severity: NotificationSeverity
    is_read: bool
    read_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, notification: Notification) -> "NotificationRead":
        return cls(
            id=notification.id,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            target_user_id=notification.target_user_id,
            target_student_id=notification.target_student_id,
            target_teacher_id=notification.target_teacher_id,
            class_id=notification.class_id,
            severity=notification.severity,
            is_read=notification.is_read,
            read_at=notification.read_at,
            created_at=notification.created_at,
            updated_at=notification.updated_at,
        )


class NotificationUnreadCountRead(BaseModel):
    unread_count: int


class NotificationProgressCheckRead(BaseModel):
    created_count: int
    notifications: list[NotificationRead]
