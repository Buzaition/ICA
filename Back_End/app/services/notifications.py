from datetime import UTC, datetime
from http import HTTPStatus

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.domain.enums import NotificationSeverity, NotificationType, UserRole
from app.models.notification import Notification
from app.models.user import User
from app.repositories.academic import AcademicRepository
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.notifications import NotificationRepository
from app.services.progress import ProgressService


class NotificationService:
    STUDENT_LOW_PROGRESS_THRESHOLD = 50
    INSTRUCTOR_LOW_PROGRESS_THRESHOLD = 50
    MENTOR_LOW_PROGRESS_THRESHOLD = 70

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.academic = AcademicRepository(session)
        self.audit_logs = AuditLogRepository(session)
        self.notifications = NotificationRepository(session)
        self.progress_service = ProgressService(session)

    async def list_notifications(self, actor: User) -> list[Notification]:
        self._require_admin(actor)
        return await self.notifications.list_all()

    async def unread_count(self, actor: User) -> int:
        self._require_admin(actor)
        return await self.notifications.unread_count()

    async def check_progress(self, actor: User) -> list[Notification]:
        self._require_admin(actor)
        created: list[Notification] = []
        classes = await self.academic.list_classes()
        teacher_ids = set()
        for academic_class in classes:
            class_progress = await self.progress_service.get_class_progress_for_user(academic_class.id, actor)
            for student_progress in class_progress.students:
                if student_progress.final_progress < self.STUDENT_LOW_PROGRESS_THRESHOLD:
                    notification = await self._create_if_missing(
                        Notification(
                            type=NotificationType.student_low_progress,
                            title="Student low progress",
                            message=(
                                f"{student_progress.student_name} progress is "
                                f"{student_progress.final_progress}% in class {student_progress.class_code}."
                            ),
                            target_student_id=student_progress.student_id,
                            class_id=student_progress.class_id,
                            severity=NotificationSeverity.warning,
                        )
                    )
                    if notification is not None:
                        created.append(notification)
            teacher_ids.add(academic_class.instructor_id)
            teacher_ids.add(academic_class.mentor_id)
        for teacher_id in teacher_ids:
            teacher_progress = await self.progress_service.get_teacher_progress(teacher_id, actor)
            for assigned_class in teacher_progress.assigned_classes:
                if (
                    assigned_class.role == "instructor"
                    and assigned_class.class_progress < self.INSTRUCTOR_LOW_PROGRESS_THRESHOLD
                ):
                    notification = await self._create_if_missing(
                        Notification(
                            type=NotificationType.instructor_low_progress,
                            title="Instructor low progress",
                            message=(
                                f"{teacher_progress.teacher_name} instructor progress is "
                                f"{assigned_class.class_progress}% in class {assigned_class.class_code}."
                            ),
                            target_teacher_id=teacher_progress.teacher_id,
                            class_id=assigned_class.class_id,
                            severity=NotificationSeverity.warning,
                        )
                    )
                    if notification is not None:
                        created.append(notification)
                if assigned_class.role == "mentor":
                    mentor_progress = 50 + (assigned_class.class_progress / 2)
                    if mentor_progress < self.MENTOR_LOW_PROGRESS_THRESHOLD:
                        notification = await self._create_if_missing(
                            Notification(
                                type=NotificationType.mentor_low_progress,
                                title="Mentor low progress",
                                message=(
                                    f"{teacher_progress.teacher_name} mentor progress is "
                                    f"{round(mentor_progress, 2)}% in class {assigned_class.class_code}."
                                ),
                                target_teacher_id=teacher_progress.teacher_id,
                                class_id=assigned_class.class_id,
                                severity=NotificationSeverity.warning,
                            )
                        )
                        if notification is not None:
                            created.append(notification)
        if created:
            await self.audit_logs.add(
                actor.id,
                "check_progress_notifications",
                "notification",
                None,
                new_value={"created_count": len(created)},
            )
        await self.session.commit()
        return await self._refresh_created(created)

    async def mark_read(self, notification_id, actor: User) -> Notification:
        self._require_admin(actor)
        notification = await self.notifications.get_by_id(notification_id)
        if notification is None:
            raise AppException("Notification not found", HTTPStatus.NOT_FOUND)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(UTC)
            await self.audit_logs.add(
                actor.id,
                "mark_notification_read",
                "notification",
                notification.id,
                new_value={"is_read": True},
            )
            await self.session.commit()
        return await self._require_notification(notification.id)

    async def mark_all_read(self, actor: User) -> list[Notification]:
        self._require_admin(actor)
        unread = await self.notifications.list_unread()
        now = datetime.now(UTC)
        for notification in unread:
            notification.is_read = True
            notification.read_at = now
        if unread:
            await self.audit_logs.add(
                actor.id,
                "mark_all_notifications_read",
                "notification",
                None,
                new_value={"marked_count": len(unread)},
            )
        await self.session.commit()
        return await self.notifications.list_all()

    async def _create_if_missing(self, notification: Notification) -> Notification | None:
        duplicate = await self.notifications.get_duplicate_unread(
            notification.type,
            notification.class_id,
            notification.target_user_id,
            notification.target_student_id,
            notification.target_teacher_id,
        )
        if duplicate is not None:
            return None
        try:
            return await self.notifications.add(notification)
        except IntegrityError:
            await self.session.rollback()
            return None

    async def _refresh_created(self, notifications: list[Notification]) -> list[Notification]:
        refreshed = []
        for notification in notifications:
            refreshed.append(await self._require_notification(notification.id))
        return refreshed

    async def _require_notification(self, notification_id) -> Notification:
        notification = await self.notifications.get_by_id(notification_id)
        if notification is None:
            raise AppException("Notification not found", HTTPStatus.NOT_FOUND)
        return notification

    def _require_admin(self, actor: User) -> None:
        if actor.role != UserRole.admin:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
