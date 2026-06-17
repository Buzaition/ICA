from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.enums import ClassStatus
from app.models.academic import Branch, Class, Cycle, Level, Track
from app.models.profiles import TeacherProfile


class AcademicRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, entity):
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def get_branch(self, branch_id: UUID, include_deleted: bool = False) -> Branch | None:
        statement = select(Branch).where(Branch.id == branch_id)
        if not include_deleted:
            statement = statement.where(Branch.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def get_branch_by_name(self, name: str, include_deleted: bool = False) -> Branch | None:
        statement = select(Branch).where(Branch.name == name)
        if not include_deleted:
            statement = statement.where(Branch.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def list_branches(self) -> list[Branch]:
        result = await self.session.scalars(
            select(Branch).where(Branch.deleted_at.is_(None)).order_by(Branch.name)
        )
        return list(result.all())

    async def get_cycle(self, cycle_id: UUID, include_deleted: bool = False) -> Cycle | None:
        statement = select(Cycle).where(Cycle.id == cycle_id)
        if not include_deleted:
            statement = statement.where(Cycle.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def get_cycle_by_number(self, cycle_number: int, include_deleted: bool = False) -> Cycle | None:
        statement = select(Cycle).where(Cycle.cycle_number == cycle_number)
        if not include_deleted:
            statement = statement.where(Cycle.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def list_cycles(self) -> list[Cycle]:
        result = await self.session.scalars(
            select(Cycle).where(Cycle.deleted_at.is_(None)).order_by(Cycle.cycle_number)
        )
        return list(result.all())

    async def get_track(self, track_id: UUID, include_deleted: bool = False) -> Track | None:
        statement = (
            select(Track)
            .options(selectinload(Track.levels.and_(Level.deleted_at.is_(None))))
            .where(Track.id == track_id)
        )
        if not include_deleted:
            statement = statement.where(Track.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def get_track_by_code(self, code: str, include_deleted: bool = False) -> Track | None:
        statement = select(Track).where(Track.code == code.upper())
        if not include_deleted:
            statement = statement.where(Track.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def get_track_by_name_or_number(
        self,
        name: str,
        track_number: int,
        include_deleted: bool = False,
    ) -> Track | None:
        statement = select(Track).where(or_(Track.name == name, Track.track_number == track_number))
        if not include_deleted:
            statement = statement.where(Track.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def list_tracks(self) -> list[Track]:
        result = await self.session.scalars(
            select(Track)
            .options(selectinload(Track.levels.and_(Level.deleted_at.is_(None))))
            .where(Track.deleted_at.is_(None))
            .order_by(Track.track_number)
        )
        return list(result.all())

    async def get_level(self, level_id: UUID, include_deleted: bool = False) -> Level | None:
        statement = select(Level).options(selectinload(Level.track)).where(Level.id == level_id)
        if not include_deleted:
            statement = statement.where(Level.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def get_level_by_track_and_number(
        self,
        track_id: UUID,
        level_number: int,
        include_deleted: bool = False,
    ) -> Level | None:
        statement = select(Level).where(Level.track_id == track_id, Level.level_number == level_number)
        if not include_deleted:
            statement = statement.where(Level.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def list_levels(self) -> list[Level]:
        result = await self.session.scalars(
            select(Level)
            .options(selectinload(Level.track))
            .where(Level.deleted_at.is_(None))
            .order_by(Level.track_id, Level.level_number)
        )
        return list(result.all())

    async def get_class(self, class_id: UUID, include_deleted: bool = False) -> Class | None:
        statement = self._class_query().where(Class.id == class_id)
        if not include_deleted:
            statement = statement.where(Class.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def get_class_by_code(self, code: str, include_deleted: bool = False) -> Class | None:
        statement = self._class_query().where(Class.code == code.upper())
        if not include_deleted:
            statement = statement.where(Class.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def list_classes(self) -> list[Class]:
        result = await self.session.scalars(
            self._class_query().where(Class.deleted_at.is_(None)).order_by(Class.created_at.desc())
        )
        return list(result.all())

    async def list_classes_for_teacher(self, teacher_profile_id: UUID) -> list[Class]:
        result = await self.session.scalars(
            self._class_query()
            .where(
                Class.deleted_at.is_(None),
                or_(Class.instructor_id == teacher_profile_id, Class.mentor_id == teacher_profile_id),
            )
            .order_by(Class.created_at.desc())
        )
        return list(result.all())

    async def list_active_classes_for_track(self, track_id: UUID) -> list[Class]:
        result = await self.session.scalars(
            self._class_query()
            .where(
                Class.track_id == track_id,
                Class.status == ClassStatus.active,
                Class.deleted_at.is_(None),
            )
            .order_by(Class.created_at.desc())
        )
        return list(result.all())

    async def get_teacher_profile(self, teacher_profile_id: UUID) -> TeacherProfile | None:
        return await self.session.scalar(select(TeacherProfile).where(TeacherProfile.id == teacher_profile_id))

    def _class_query(self):
        return select(Class).options(
            selectinload(Class.branch),
            selectinload(Class.cycle),
            selectinload(Class.track),
            selectinload(Class.level),
            selectinload(Class.instructor),
            selectinload(Class.mentor),
        )
