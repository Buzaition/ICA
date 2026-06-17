import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import MaterialCreatorRole, MaterialType

if TYPE_CHECKING:
    from app.models.academic import Class
    from app.models.profiles import TeacherProfile


class Material(Base):
    __tablename__ = "materials"
    __table_args__ = (
        Index("ix_materials_class_id", "class_id"),
        Index("ix_materials_creator_id", "creator_id"),
        Index("ix_materials_material_type", "material_type"),
        Index("ix_materials_creator_role", "creator_role"),
        Index("ix_materials_deleted_at", "deleted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id"), nullable=False)
    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teacher_profiles.id"), nullable=False)
    creator_role: Mapped[MaterialCreatorRole] = mapped_column(
        Enum(MaterialCreatorRole, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    material_type: Mapped[MaterialType] = mapped_column(
        Enum(MaterialType, values_callable=lambda enum: [item.value for item in enum], native_enum=False),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
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
    creator: Mapped["TeacherProfile"] = relationship()
