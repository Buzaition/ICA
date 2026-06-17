import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.academic import Class
    from app.models.profiles import StudentProfile


class ProgressSnapshot(Base):
    __tablename__ = "progress_snapshots"
    __table_args__ = (
        Index("ix_progress_snapshots_student_id", "student_id"),
        Index("ix_progress_snapshots_class_id", "class_id"),
        Index("ix_progress_snapshots_week_number", "week_number"),
        Index("ix_progress_snapshots_year", "year"),
        Index("ix_progress_snapshots_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.id"), nullable=False)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id"), nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    attendance_progress: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quiz_progress: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    assignment_progress: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    bonus_progress: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    final_progress: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    student: Mapped["StudentProfile"] = relationship()
    academic_class: Mapped["Class"] = relationship()
