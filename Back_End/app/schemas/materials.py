from datetime import datetime
from uuid import UUID

from pydantic import AnyUrl, BaseModel, Field

from app.domain.enums import MaterialCreatorRole, MaterialType
from app.models.material import Material


class MaterialCreate(BaseModel):
    class_id: UUID
    creator_id: UUID | None = None
    creator_role: MaterialCreatorRole
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    material_type: MaterialType
    url: AnyUrl


class MaterialUpdate(BaseModel):
    creator_role: MaterialCreatorRole | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    material_type: MaterialType | None = None
    url: AnyUrl | None = None
    is_active: bool | None = None


class MaterialRead(BaseModel):
    id: UUID
    class_id: UUID
    class_code: str
    creator_id: UUID
    creator_name: str
    creator_role: MaterialCreatorRole
    title: str
    description: str | None
    material_type: MaterialType
    url: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, material: Material) -> "MaterialRead":
        return cls(
            id=material.id,
            class_id=material.class_id,
            class_code=material.academic_class.code,
            creator_id=material.creator_id,
            creator_name=material.creator.full_name,
            creator_role=material.creator_role,
            title=material.title,
            description=material.description,
            material_type=material.material_type,
            url=material.url,
            created_at=material.created_at,
            updated_at=material.updated_at,
        )
