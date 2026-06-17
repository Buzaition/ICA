import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import QuizSourceType

if TYPE_CHECKING:
    from app.models.academic import Class
    from app.models.grade import GradeEntry
    from app.models.profiles import StudentProfile, TeacherProfile
    from app.models.user import User


class Quiz(Base):
    __tablename__ = "quizzes"
    __table_args__ = (
        Index("ix_quizzes_class_id", "class_id"),
        Index("ix_quizzes_teacher_id", "teacher_id"),
        Index("ix_quizzes_quiz_date", "quiz_date"),
        Index("ix_quizzes_deleted_at", "deleted_at"),
        Index(
            "uq_quizzes_active_identity",
            "class_id",
            "teacher_id",
            "title",
            "quiz_date",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teacher_profiles.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quiz_date: Mapped[date] = mapped_column(Date, nullable=False)
    max_grade: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    source_type: Mapped[QuizSourceType] = mapped_column(
        Enum(QuizSourceType, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
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
    results: Mapped[list["QuizResult"]] = relationship(back_populates="quiz")


class QuizResult(Base):
    __tablename__ = "quiz_results"
    __table_args__ = (
        Index("ix_quiz_results_quiz_id", "quiz_id"),
        Index("ix_quiz_results_student_id", "student_id"),
        Index("ix_quiz_results_deleted_at", "deleted_at"),
        Index(
            "uq_quiz_results_active_quiz_student",
            "quiz_id",
            "student_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quizzes.id"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.id"), nullable=False)
    earned_grade: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    max_grade: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    grade_entry_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("grade_entries.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    quiz: Mapped["Quiz"] = relationship(back_populates="results")
    student: Mapped["StudentProfile"] = relationship()
    grade_entry: Mapped["GradeEntry | None"] = relationship()
