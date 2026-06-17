import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import FinalProjectStatus

if TYPE_CHECKING:
    from app.models.academic import Class, Level
    from app.models.profiles import AdminProfile, StudentProfile


class FinalProject(Base):
    __tablename__ = "final_projects"
    __table_args__ = (
        Index("ix_final_projects_student_id", "student_id"),
        Index("ix_final_projects_class_id", "class_id"),
        Index("ix_final_projects_level_id", "level_id"),
        Index("ix_final_projects_status", "status"),
        Index("ix_final_projects_deleted_at", "deleted_at"),
        Index(
            "uq_final_projects_active_student_class_level",
            "student_id",
            "class_id",
            "level_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.id"), nullable=False)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id"), nullable=False)
    level_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("levels.id"), nullable=False)
    project_link: Mapped[str] = mapped_column(Text, nullable=False)
    grade: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[FinalProjectStatus] = mapped_column(
        Enum(FinalProjectStatus, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        nullable=False,
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("admin_profiles.id"), nullable=True)
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
    level: Mapped["Level"] = relationship()
    reviewed_by_admin: Mapped["AdminProfile | None"] = relationship()
