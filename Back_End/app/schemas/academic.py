from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import ClassStatus, ClassType, CycleStatus


class BranchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class BranchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class BranchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class CycleCreate(BaseModel):
    cycle_number: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=255)
    start_date: date
    end_date: date
    status: CycleStatus = CycleStatus.active


class CycleUpdate(BaseModel):
    cycle_number: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    status: CycleStatus | None = None


class CycleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cycle_number: int
    name: str
    start_date: date
    end_date: date
    status: CycleStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class TrackCreate(BaseModel):
    code: str = Field(min_length=2, max_length=2)
    name: str = Field(min_length=1, max_length=255)
    track_number: int = Field(ge=1)
    create_default_levels: bool = False

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, value: str) -> str:
        return value.upper()


class TrackUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=2)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    track_number: int | None = Field(default=None, ge=1)

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else value


class LevelCreate(BaseModel):
    track_id: UUID
    level_number: int = Field(ge=1, le=3)
    title: str = Field(min_length=1, max_length=255)
    duration_months: int = Field(default=2, ge=1)


class LevelUpdate(BaseModel):
    track_id: UUID | None = None
    level_number: int | None = Field(default=None, ge=1, le=3)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    duration_months: int | None = Field(default=None, ge=1)


class LevelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    track_id: UUID
    level_number: int
    title: str
    duration_months: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class TrackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    track_number: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    levels: list[LevelRead] = []


class ClassCreate(BaseModel):
    code: str = Field(min_length=6, max_length=6, pattern=r"^[A-Z]{2}[15][0-9]{3}$")
    branch_id: UUID
    cycle_id: UUID
    track_id: UUID
    level_id: UUID
    instructor_id: UUID
    mentor_id: UUID
    schedule_text: str = Field(min_length=1)
    max_students: int = Field(default=25, ge=1, le=25)
    class_type: ClassType
    start_date: date
    end_date: date
    status: ClassStatus = ClassStatus.planned

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, value: str) -> str:
        return value.upper()


class ClassUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=6, max_length=6, pattern=r"^[A-Z]{2}[15][0-9]{3}$")
    branch_id: UUID | None = None
    cycle_id: UUID | None = None
    track_id: UUID | None = None
    level_id: UUID | None = None
    instructor_id: UUID | None = None
    mentor_id: UUID | None = None
    schedule_text: str | None = Field(default=None, min_length=1)
    max_students: int | None = Field(default=None, ge=1, le=25)
    class_type: ClassType | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: ClassStatus | None = None

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else value


class ClassRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    branch_id: UUID
    cycle_id: UUID
    track_id: UUID
    level_id: UUID
    instructor_id: UUID
    mentor_id: UUID
    schedule_text: str
    max_students: int
    class_type: ClassType
    start_date: date
    end_date: date
    status: ClassStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
