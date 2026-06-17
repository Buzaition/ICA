import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import GradeCategory, GradeSourceType

if TYPE_CHECKING:
    from app.models.academic import Class
    from app.models.assignment import AssignmentSubmission
    from app.models.profiles import StudentProfile, TeacherProfile
    from app.models.user import User


class GradeEntry(Base):
    __tablename__ = "grade_entries"
    __table_args__ = (
        Index("ix_grade_entries_student_id", "student_id"),
        Index("ix_grade_entries_class_id", "class_id"),
        Index("ix_grade_entries_teacher_id", "teacher_id"),
        Index("ix_grade_entries_category", "category"),
        Index("ix_grade_entries_source_type", "source_type"),
        Index("ix_grade_entries_related_entry_id", "related_entry_id"),
        Index("ix_grade_entries_assignment_submission_id", "assignment_submission_id"),
        Index("ix_grade_entries_deleted_at", "deleted_at"),
        Index(
            "uq_grade_entries_assignment_submission_id_active",
            "assignment_submission_id",
            unique=True,
            postgresql_where=text("assignment_submission_id IS NOT NULL AND deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.id"), nullable=False)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id"), nullable=False)
    teacher_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teacher_profiles.id"), nullable=True)
    category: Mapped[GradeCategory] = mapped_column(
        Enum(GradeCategory, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        nullable=False,
    )
    earned_grade: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    max_grade: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    source_type: Mapped[GradeSourceType] = mapped_column(
        Enum(GradeSourceType, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    related_entry_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("grade_entries.id"), nullable=True)
    assignment_submission_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assignment_submissions.id"),
        nullable=True,
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["StudentProfile"] = relationship()
    academic_class: Mapped["Class"] = relationship()
    teacher: Mapped["TeacherProfile | None"] = relationship()
    related_entry: Mapped["GradeEntry | None"] = relationship(remote_side=[id])
    assignment_submission: Mapped["AssignmentSubmission | None"] = relationship(back_populates="grade_entries")
    created_by_user: Mapped["User"] = relationship()
