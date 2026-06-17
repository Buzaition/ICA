from collections.abc import Callable

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.db.session import get_session
from app.domain.enums import UserRole
from app.models.user import User
from app.services.auth import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    if credentials is None:
        raise AppException("Authentication required", status.HTTP_401_UNAUTHORIZED)
    return await AuthService(session).get_user_from_token(credentials.credentials)


def require_role(role: UserRole) -> Callable:
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != role:
            raise AppException("Forbidden", status.HTTP_403_FORBIDDEN)
        return current_user

    return dependency

