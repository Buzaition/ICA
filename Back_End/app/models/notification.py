import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import NotificationSeverity, NotificationType

if TYPE_CHECKING:
    from app.models.academic import Class
    from app.models.profiles import StudentProfile, TeacherProfile
    from app.models.user import User


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_type", "type"),
        Index("ix_notifications_target_user_id", "target_user_id"),
        Index("ix_notifications_target_student_id", "target_student_id"),
        Index("ix_notifications_target_teacher_id", "target_teacher_id"),
        Index("ix_notifications_class_id", "class_id"),
        Index("ix_notifications_is_read", "is_read"),
        Index("ix_notifications_deleted_at", "deleted_at"),
        Index(
            "uq_notifications_unread_target_type_class",
            "type",
            "target_user_id",
            "target_student_id",
            "target_teacher_id",
            "class_id",
            unique=True,
            postgresql_where=text("is_read = false AND deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    target_student_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("student_profiles.id"), nullable=True)
    target_teacher_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teacher_profiles.id"), nullable=True)
    class_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("classes.id"), nullable=True)
    severity: Mapped[NotificationSeverity] = mapped_column(
        Enum(NotificationSeverity, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        nullable=False,
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    target_user: Mapped["User | None"] = relationship()
    target_student: Mapped["StudentProfile | None"] = relationship()
    target_teacher: Mapped["TeacherProfile | None"] = relationship()
    academic_class: Mapped["Class | None"] = relationship()
