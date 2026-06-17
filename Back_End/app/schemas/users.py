from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.domain.enums import StudentStatus, TeacherType, UserRole


class AdminProfileCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)


class TeacherProfileCreate(BaseModel):
    teacher_code: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=1, max_length=255)
    phone_number: str | None = Field(default=None, max_length=50)
    teacher_type: TeacherType
    is_team_leader: bool = False


class StudentProfileCreate(BaseModel):
    student_code: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=1, max_length=255)
    phone_number: str | None = Field(default=None, max_length=50)
    status: StudentStatus = StudentStatus.active


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole
    admin_profile: AdminProfileCreate | None = None
    teacher_profile: TeacherProfileCreate | None = None
    student_profile: StudentProfileCreate | None = None

    @model_validator(mode="after")
    def validate_profile_for_role(self) -> "UserCreate":
        expected = {
            UserRole.admin: self.admin_profile,
            UserRole.teacher: self.teacher_profile,
            UserRole.student: self.student_profile,
        }[self.role]
        if expected is None:
            raise ValueError(f"{self.role.value}_profile is required")
        return self


class AdminProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)


class TeacherProfileUpdate(BaseModel):
    teacher_code: str | None = Field(default=None, min_length=1, max_length=50)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone_number: str | None = Field(default=None, max_length=50)
    teacher_type: TeacherType | None = None
    is_team_leader: bool | None = None


class StudentProfileUpdate(BaseModel):
    student_code: str | None = Field(default=None, min_length=1, max_length=50)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone_number: str | None = Field(default=None, max_length=50)
    status: StudentStatus | None = None


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    is_active: bool | None = None
    admin_profile: AdminProfileUpdate | None = None
    teacher_profile: TeacherProfileUpdate | None = None
    student_profile: StudentProfileUpdate | None = None


class AdminProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    full_name: str
    created_at: datetime
    updated_at: datetime


class TeacherProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    teacher_code: str
    full_name: str
    phone_number: str | None
    teacher_type: TeacherType
    is_team_leader: bool
    created_at: datetime
    updated_at: datetime


class StudentProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    student_code: str
    full_name: str
    phone_number: str | None
    status: StudentStatus
    created_at: datetime
    updated_at: datetime


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: UserRole
    is_active: bool
    must_change_password: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    admin_profile: AdminProfileRead | None = None
    teacher_profile: TeacherProfileRead | None = None
    student_profile: StudentProfileRead | None = None

