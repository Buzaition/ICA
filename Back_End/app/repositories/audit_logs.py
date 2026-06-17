from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        actor_id: UUID | None,
        action: str,
        entity_name: str,
        entity_id: UUID | None,
        old_value: dict | None = None,
        new_value: dict | None = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            actor_id=actor_id,
            action=action,
            entity_name=entity_name,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
        )
        self.session.add(audit_log)
        await self.session.flush()
        return audit_log

