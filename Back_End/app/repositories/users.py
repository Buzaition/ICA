from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profiles import AdminProfile, StudentProfile, TeacherProfile
from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: UUID, include_deleted: bool = False) -> User | None:
        statement = (
            select(User)
            .options(
                selectinload(User.admin_profile),
                selectinload(User.teacher_profile),
                selectinload(User.student_profile),
            )
            .where(User.id == user_id)
        )
        if not include_deleted:
            statement = statement.where(User.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def get_by_email(self, email: str, include_deleted: bool = False) -> User | None:
        statement = (
            select(User)
            .options(
                selectinload(User.admin_profile),
                selectinload(User.teacher_profile),
                selectinload(User.student_profile),
            )
            .where(User.email == email.lower())
        )
        if not include_deleted:
            statement = statement.where(User.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def list(self) -> list[User]:
        statement = (
            select(User)
            .options(
                selectinload(User.admin_profile),
                selectinload(User.teacher_profile),
                selectinload(User.student_profile),
            )
            .where(User.deleted_at.is_(None))
            .order_by(User.created_at.desc())
        )
        result = await self.session.scalars(statement)
        return list(result.all())

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def add_admin_profile(self, profile: AdminProfile) -> AdminProfile:
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def add_teacher_profile(self, profile: TeacherProfile) -> TeacherProfile:
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def add_student_profile(self, profile: StudentProfile) -> StudentProfile:
        self.session.add(profile)
        await self.session.flush()
        return profile

