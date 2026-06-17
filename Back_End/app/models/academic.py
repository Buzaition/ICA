import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import ClassStatus, ClassType, CycleStatus

if TYPE_CHECKING:
    from app.models.profiles import TeacherProfile


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    classes: Mapped[list["Class"]] = relationship(back_populates="branch")


class Cycle(Base):
    __tablename__ = "cycles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[CycleStatus] = mapped_column(
        Enum(CycleStatus, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    classes: Mapped[list["Class"]] = relationship(back_populates="cycle")


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    track_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    levels: Mapped[list["Level"]] = relationship(back_populates="track", cascade="all, delete-orphan")
    classes: Mapped[list["Class"]] = relationship(back_populates="track")


class Level(Base):
    __tablename__ = "levels"
    __table_args__ = (
        UniqueConstraint("track_id", "level_number", name="uq_levels_track_id_level_number"),
        CheckConstraint("level_number IN (1, 2, 3)", name="ck_levels_level_number_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id"), nullable=False)
    level_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_months: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    track: Mapped["Track"] = relationship(back_populates="levels")
    classes: Mapped[list["Class"]] = relationship(back_populates="level")


class Class(Base):
    __tablename__ = "classes"
    __table_args__ = (CheckConstraint("max_students <= 25", name="ck_classes_max_students_limit"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(6), unique=True, nullable=False)
    branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.id"), nullable=False)
    cycle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cycles.id"), nullable=False)
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id"), nullable=False)
    level_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("levels.id"), nullable=False)
    instructor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teacher_profiles.id"), nullable=False)
    mentor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teacher_profiles.id"), nullable=False)
    schedule_text: Mapped[str] = mapped_column(Text, nullable=False)
    max_students: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    class_type: Mapped[ClassType] = mapped_column(
        Enum(ClassType, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ClassStatus] = mapped_column(
        Enum(ClassStatus, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    branch: Mapped["Branch"] = relationship(back_populates="classes")
    cycle: Mapped["Cycle"] = relationship(back_populates="classes")
    track: Mapped["Track"] = relationship(back_populates="classes")
    level: Mapped["Level"] = relationship(back_populates="classes")
    instructor: Mapped["TeacherProfile"] = relationship(foreign_keys=[instructor_id])
    mentor: Mapped["TeacherProfile"] = relationship(foreign_keys=[mentor_id])
