from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from uuid import UUID

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.security import (
    create_access_token,
    create_refresh_token_value,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.repositories.users import UserRepository
from app.schemas.auth import TokenPair


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.refresh_tokens = RefreshTokenRepository(session)
        self.audit_logs = AuditLogRepository(session)

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self.users.get_by_email(email)
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            raise AppException("Invalid credentials", HTTPStatus.UNAUTHORIZED)
        token_pair = await self._create_token_pair(user)
        await self.audit_logs.add(user.id, "login", "user", user.id)
        await self.session.commit()
        return token_pair

    async def refresh(self, refresh_token_value: str) -> TokenPair:
        refresh_token = await self.refresh_tokens.get_active_by_hash(hash_refresh_token(refresh_token_value))
        if refresh_token is None or refresh_token.user.deleted_at is not None or not refresh_token.user.is_active:
            raise AppException("Invalid refresh token", HTTPStatus.UNAUTHORIZED)
        await self.refresh_tokens.revoke(refresh_token)
        token_pair = await self._create_token_pair(refresh_token.user)
        await self.audit_logs.add(refresh_token.user_id, "refresh_token", "user", refresh_token.user_id)
        await self.session.commit()
        return token_pair

    async def logout(self, refresh_token_value: str, actor: User) -> None:
        refresh_token = await self.refresh_tokens.get_active_by_hash(hash_refresh_token(refresh_token_value))
        if refresh_token is not None and refresh_token.user_id == actor.id:
            await self.refresh_tokens.revoke(refresh_token)
        await self.audit_logs.add(actor.id, "logout", "user", actor.id)
        await self.session.commit()

    async def change_password(self, actor: User, current_password: str, new_password: str) -> None:
        user = await self.users.get_by_id(actor.id)
        if user is None or not verify_password(current_password, user.password_hash):
            raise AppException("Current password is incorrect", HTTPStatus.BAD_REQUEST)
        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.audit_logs.add(actor.id, "change_password", "user", user.id)
        await self.session.commit()

    async def reset_password(self, actor: User, user_id: UUID, new_password: str) -> None:
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise AppException("User not found", HTTPStatus.NOT_FOUND)
        user.password_hash = hash_password(new_password)
        user.must_change_password = True
        await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.audit_logs.add(actor.id, "reset_password", "user", user.id)
        await self.session.commit()

    async def get_user_from_token(self, token: str) -> User:
        try:
            payload = decode_access_token(token)
            user_id = UUID(payload["sub"])
        except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
            raise AppException("Invalid authentication token", HTTPStatus.UNAUTHORIZED) from exc
        user = await self.users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AppException("Invalid authentication token", HTTPStatus.UNAUTHORIZED)
        return user

    async def _create_token_pair(self, user: User) -> TokenPair:
        refresh_token_value = create_refresh_token_value()
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token_value),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
        )
        await self.refresh_tokens.add(refresh_token)
        return TokenPair(
            access_token=create_access_token(user.id, user.role.value),
            refresh_token=refresh_token_value,
        )
