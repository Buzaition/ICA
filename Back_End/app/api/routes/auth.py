from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.responses import success_response
from app.db.session import get_session
from app.domain.enums import UserRole
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LogoutRequest, RefreshRequest, ResetPasswordRequest
from app.schemas.users import UserRead
from app.services.auth import AuthService

router = APIRouter()


@router.post("/login")
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)) -> dict:
    token_pair = await AuthService(session).login(payload.email, payload.password)
    return success_response(data=token_pair.model_dump())


@router.post("/refresh")
async def refresh(payload: RefreshRequest, session: AsyncSession = Depends(get_session)) -> dict:
    token_pair = await AuthService(session).refresh(payload.refresh_token)
    return success_response(data=token_pair.model_dump())


@router.post("/logout")
async def logout(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await AuthService(session).logout(payload.refresh_token, current_user)
    return success_response()


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await AuthService(session).change_password(current_user, payload.current_password, payload.new_password)
    return success_response()


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await AuthService(session).reset_password(current_user, payload.user_id, payload.new_password)
    return success_response()


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)) -> dict:
    return success_response(data=UserRead.model_validate(current_user).model_dump(mode="json"))

