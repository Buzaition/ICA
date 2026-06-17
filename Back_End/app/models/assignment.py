import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import AssignmentSubmissionStatus

if TYPE_CHECKING:
    from app.models.academic import Class
    from app.models.grade import GradeEntry
    from app.models.profiles import StudentProfile, TeacherProfile


class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (
        Index("ix_assignments_class_id", "class_id"),
        Index("ix_assignments_created_by_teacher_id", "created_by_teacher_id"),
        Index("ix_assignments_deadline", "deadline"),
        Index("ix_assignments_deleted_at", "deleted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id"), nullable=False)
    created_by_teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teacher_profiles.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirement_url: Mapped[str] = mapped_column(Text, nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_grade: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    academic_class: Mapped["Class"] = relationship()
    created_by_teacher: Mapped["TeacherProfile"] = relationship()
    submissions: Mapped[list["AssignmentSubmission"]] = relationship(back_populates="assignment")


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"
    __table_args__ = (
        Index("ix_assignment_submissions_assignment_id", "assignment_id"),
        Index("ix_assignment_submissions_student_id", "student_id"),
        Index("ix_assignment_submissions_status", "status"),
        Index("ix_assignment_submissions_reviewed_at", "reviewed_at"),
        Index("ix_assignment_submissions_deleted_at", "deleted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assignments.id"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.id"), nullable=False)
    submission_url: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    grade: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[AssignmentSubmissionStatus] = mapped_column(
        Enum(AssignmentSubmissionStatus, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        nullable=False,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_teacher_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teacher_profiles.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assignment: Mapped["Assignment"] = relationship(back_populates="submissions")
    student: Mapped["StudentProfile"] = relationship()
    reviewed_by_teacher: Mapped["TeacherProfile | None"] = relationship()
    grade_entries: Mapped[list["GradeEntry"]] = relationship(back_populates="assignment_submission")
