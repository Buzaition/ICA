from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import hash_password
from app.domain.enums import UserRole
from app.models.profiles import AdminProfile, StudentProfile, TeacherProfile
from app.models.user import User
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.repositories.users import UserRepository
from app.schemas.users import UserCreate, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.refresh_tokens = RefreshTokenRepository(session)
        self.audit_logs = AuditLogRepository(session)

    async def create_user(self, payload: UserCreate, actor: User | None = None) -> User:
        existing_user = await self.users.get_by_email(payload.email, include_deleted=True)
        if existing_user is not None:
            raise AppException("Email already exists", HTTPStatus.CONFLICT)
        user = User(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            role=payload.role,
            is_active=True,
            must_change_password=True,
        )
        try:
            await self.users.add(user)
            await self._create_profile(user, payload)
            await self.audit_logs.add(
                actor.id if actor else None,
                "create_user",
                "user",
                user.id,
                new_value={"email": user.email, "role": user.role.value},
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppException("User data must be unique", HTTPStatus.CONFLICT) from exc
        return await self._require_user(user.id)

    async def list_users(self) -> list[User]:
        return await self.users.list()

    async def get_user(self, user_id: UUID) -> User:
        return await self._require_user(user_id)

    async def update_user(self, user_id: UUID, payload: UserUpdate, actor: User) -> User:
        user = await self._require_user(user_id)
        old_value = {"email": user.email, "is_active": user.is_active}
        update_data = payload.model_dump(exclude_unset=True)
        if "email" in update_data and update_data["email"] is not None:
            existing_user = await self.users.get_by_email(update_data["email"], include_deleted=True)
            if existing_user is not None and existing_user.id != user.id:
                raise AppException("Email already exists", HTTPStatus.CONFLICT)
            user.email = update_data["email"].lower()
        if "is_active" in update_data and update_data["is_active"] is not None:
            user.is_active = update_data["is_active"]
        self._update_profile(user, payload)
        try:
            await self.audit_logs.add(
                actor.id,
                "update_user",
                "user",
                user.id,
                old_value=old_value,
                new_value={"email": user.email, "is_active": user.is_active},
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppException("User data must be unique", HTTPStatus.CONFLICT) from exc
        return await self._require_user(user.id)

    async def soft_delete_user(self, user_id: UUID, actor: User) -> None:
        user = await self._require_user(user_id)
        user.deleted_at = datetime.now(UTC)
        user.is_active = False
        await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.audit_logs.add(actor.id, "delete_user", "user", user.id)
        await self.session.commit()

    async def _require_user(self, user_id: UUID) -> User:
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise AppException("User not found", HTTPStatus.NOT_FOUND)
        return user

    async def _create_profile(self, user: User, payload: UserCreate) -> None:
        if payload.role == UserRole.admin and payload.admin_profile is not None:
            await self.users.add_admin_profile(AdminProfile(user_id=user.id, **payload.admin_profile.model_dump()))
        elif payload.role == UserRole.teacher and payload.teacher_profile is not None:
            await self.users.add_teacher_profile(TeacherProfile(user_id=user.id, **payload.teacher_profile.model_dump()))
        elif payload.role == UserRole.student and payload.student_profile is not None:
            await self.users.add_student_profile(StudentProfile(user_id=user.id, **payload.student_profile.model_dump()))

    def _update_profile(self, user: User, payload: UserUpdate) -> None:
        if user.role == UserRole.admin and user.admin_profile is not None and payload.admin_profile is not None:
            for field, value in payload.admin_profile.model_dump(exclude_unset=True).items():
                setattr(user.admin_profile, field, value)
        elif user.role == UserRole.teacher and user.teacher_profile is not None and payload.teacher_profile is not None:
            for field, value in payload.teacher_profile.model_dump(exclude_unset=True).items():
                setattr(user.teacher_profile, field, value)
        elif user.role == UserRole.student and user.student_profile is not None and payload.student_profile is not None:
            for field, value in payload.student_profile.model_dump(exclude_unset=True).items():
                setattr(user.student_profile, field, value)
