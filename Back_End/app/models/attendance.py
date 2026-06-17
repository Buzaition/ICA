import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import AttendanceSessionType, AttendanceSourceType, AttendanceStatus

if TYPE_CHECKING:
    from app.models.academic import Class
    from app.models.grade import GradeEntry
    from app.models.profiles import StudentProfile, TeacherProfile
    from app.models.user import User


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"
    __table_args__ = (
        Index("ix_attendance_sessions_class_id", "class_id"),
        Index("ix_attendance_sessions_teacher_id", "teacher_id"),
        Index("ix_attendance_sessions_session_date", "session_date"),
        Index("ix_attendance_sessions_session_type", "session_type"),
        Index("ix_attendance_sessions_deleted_at", "deleted_at"),
        Index(
            "uq_attendance_sessions_active_identity",
            "class_id",
            "teacher_id",
            "session_type",
            "session_date",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teacher_profiles.id"), nullable=False)
    session_type: Mapped[AttendanceSessionType] = mapped_column(
        Enum(AttendanceSessionType, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        nullable=False,
    )
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    max_grade: Mapped[float] = mapped_column(Numeric(10, 2), default=1, nullable=False)
    source_type: Mapped[AttendanceSourceType] = mapped_column(
        Enum(AttendanceSourceType, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        nullable=False,
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    academic_class: Mapped["Class"] = relationship()
    teacher: Mapped["TeacherProfile"] = relationship()
    created_by_user: Mapped["User"] = relationship()
    records: Mapped[list["AttendanceRecord"]] = relationship(back_populates="attendance_session")


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        Index("ix_attendance_records_attendance_session_id", "attendance_session_id"),
        Index("ix_attendance_records_student_id", "student_id"),
        Index("ix_attendance_records_status", "status"),
        Index("ix_attendance_records_deleted_at", "deleted_at"),
        Index(
            "uq_attendance_records_active_session_student",
            "attendance_session_id",
            "student_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attendance_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attendance_sessions.id"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.id"), nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        nullable=False,
    )
    grade_entry_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("grade_entries.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    attendance_session: Mapped["AttendanceSession"] = relationship(back_populates="records")
    student: Mapped["StudentProfile"] = relationship()
    grade_entry: Mapped["GradeEntry | None"] = relationship()
