from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.domain.enums import UserRole
from app.schemas.users import UserRead


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=32)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)


class ResetPasswordRequest(BaseModel):
    user_id: UUID
    new_password: str = Field(min_length=8)


class TokenPayload(BaseModel):
    sub: UUID
    role: UserRole


class MeResponse(UserRead):
    pass

