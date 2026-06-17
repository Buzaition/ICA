from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.responses import success_response
from app.db.session import get_session
from app.domain.enums import UserRole
from app.models.user import User
from app.schemas.users import UserCreate, UserRead, UserUpdate
from app.services.users import UserService

router = APIRouter()


@router.post("")
async def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await UserService(session).create_user(payload, current_user)
    return success_response(data=UserRead.model_validate(user).model_dump(mode="json"))


@router.get("")
async def list_users(
    _: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    users = await UserService(session).list_users()
    return success_response(data=[UserRead.model_validate(user).model_dump(mode="json") for user in users])


@router.get("/{user_id}")
async def get_user(
    user_id: UUID,
    _: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await UserService(session).get_user(user_id)
    return success_response(data=UserRead.model_validate(user).model_dump(mode="json"))


@router.put("/{user_id}")
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await UserService(session).update_user(user_id, payload, current_user)
    return success_response(data=UserRead.model_validate(user).model_dump(mode="json"))


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await UserService(session).soft_delete_user(user_id, current_user)
    return success_response()

