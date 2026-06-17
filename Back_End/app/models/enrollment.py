import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import EnrollmentStatus

if TYPE_CHECKING:
    from app.models.academic import Class
    from app.models.profiles import StudentProfile


class ClassEnrollment(Base):
    __tablename__ = "class_enrollments"
    __table_args__ = (
        Index("ix_class_enrollments_student_id", "student_id"),
        Index("ix_class_enrollments_class_id", "class_id"),
        Index("ix_class_enrollments_status", "status"),
        Index(
            "uq_class_enrollments_one_active_per_student",
            "student_id",
            unique=True,
            postgresql_where=text("status = 'active' AND deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.id"), nullable=False)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id"), nullable=False)
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        nullable=False,
    )
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["StudentProfile"] = relationship()
    academic_class: Mapped["Class"] = relationship()
