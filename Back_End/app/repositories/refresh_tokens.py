from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, refresh_token: RefreshToken) -> RefreshToken:
        self.session.add(refresh_token)
        await self.session.flush()
        return refresh_token

    async def get_active_by_hash(self, token_hash: str) -> RefreshToken | None:
        statement = (
            select(RefreshToken)
            .options(selectinload(RefreshToken.user))
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.now(UTC),
            )
        )
        return await self.session.scalar(statement)

    async def revoke(self, refresh_token: RefreshToken) -> None:
        refresh_token.revoked_at = datetime.now(UTC)
        await self.session.flush()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )

