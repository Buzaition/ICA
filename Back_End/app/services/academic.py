from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.domain.enums import ClassType, UserRole
from app.models.academic import Branch, Class as AcademicClass, Cycle, Level, Track
from app.models.user import User
from app.repositories.academic import AcademicRepository
from app.repositories.audit_logs import AuditLogRepository
from app.schemas.academic import (
    BranchCreate,
    BranchUpdate,
    ClassCreate,
    ClassUpdate,
    CycleCreate,
    CycleUpdate,
    LevelCreate,
    LevelUpdate,
    TrackCreate,
    TrackUpdate,
)


class AcademicService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.academic = AcademicRepository(session)
        self.audit_logs = AuditLogRepository(session)

    async def create_branch(self, payload: BranchCreate, actor: User | None) -> Branch:
        if await self.academic.get_branch_by_name(payload.name, include_deleted=True) is not None:
            raise AppException("Branch name already exists", HTTPStatus.CONFLICT)
        branch = Branch(name=payload.name)
        return await self._create_entity(branch, actor, "branch", {"name": payload.name})

    async def list_branches(self) -> list[Branch]:
        return await self.academic.list_branches()

    async def get_branch(self, branch_id: UUID) -> Branch:
        branch = await self.academic.get_branch(branch_id)
        if branch is None:
            raise AppException("Branch not found", HTTPStatus.NOT_FOUND)
        return branch

    async def update_branch(self, branch_id: UUID, payload: BranchUpdate, actor: User) -> Branch:
        branch = await self.get_branch(branch_id)
        old_value = {"name": branch.name}
        if payload.name is not None:
            existing = await self.academic.get_branch_by_name(payload.name, include_deleted=True)
            if existing is not None and existing.id != branch.id:
                raise AppException("Branch name already exists", HTTPStatus.CONFLICT)
            branch.name = payload.name
        await self._commit_update(actor, "branch", branch.id, old_value, {"name": branch.name})
        return await self.get_branch(branch.id)

    async def delete_branch(self, branch_id: UUID, actor: User) -> None:
        branch = await self.get_branch(branch_id)
        await self._soft_delete(branch, actor, "branch")

    async def create_cycle(self, payload: CycleCreate, actor: User | None) -> Cycle:
        if await self.academic.get_cycle_by_number(payload.cycle_number, include_deleted=True) is not None:
            raise AppException("Cycle number already exists", HTTPStatus.CONFLICT)
        cycle = Cycle(**payload.model_dump())
        return await self._create_entity(cycle, actor, "cycle", {"cycle_number": payload.cycle_number})

    async def list_cycles(self) -> list[Cycle]:
        return await self.academic.list_cycles()

    async def get_cycle(self, cycle_id: UUID) -> Cycle:
        cycle = await self.academic.get_cycle(cycle_id)
        if cycle is None:
            raise AppException("Cycle not found", HTTPStatus.NOT_FOUND)
        return cycle

    async def update_cycle(self, cycle_id: UUID, payload: CycleUpdate, actor: User) -> Cycle:
        cycle = await self.get_cycle(cycle_id)
        old_value = {"cycle_number": cycle.cycle_number, "name": cycle.name, "status": cycle.status.value}
        update_data = payload.model_dump(exclude_unset=True)
        if "cycle_number" in update_data:
            existing = await self.academic.get_cycle_by_number(update_data["cycle_number"], include_deleted=True)
            if existing is not None and existing.id != cycle.id:
                raise AppException("Cycle number already exists", HTTPStatus.CONFLICT)
        for field, value in update_data.items():
            setattr(cycle, field, value)
        await self._commit_update(
            actor,
            "cycle",
            cycle.id,
            old_value,
            {"cycle_number": cycle.cycle_number, "name": cycle.name, "status": cycle.status.value},
        )
        return await self.get_cycle(cycle.id)

    async def delete_cycle(self, cycle_id: UUID, actor: User) -> None:
        cycle = await self.get_cycle(cycle_id)
        await self._soft_delete(cycle, actor, "cycle")

    async def create_track(self, payload: TrackCreate, actor: User | None) -> Track:
        if await self.academic.get_track_by_code(payload.code, include_deleted=True) is not None:
            raise AppException("Track code already exists", HTTPStatus.CONFLICT)
        if await self.academic.get_track_by_name_or_number(payload.name, payload.track_number, True) is not None:
            raise AppException("Track name or number already exists", HTTPStatus.CONFLICT)
        track = Track(code=payload.code, name=payload.name, track_number=payload.track_number)
        try:
            await self.academic.add(track)
            if payload.create_default_levels:
                await self._create_default_levels(track)
            await self.audit_logs.add(
                actor.id if actor else None,
                "create_track",
                "track",
                track.id,
                new_value={"code": track.code, "name": track.name, "track_number": track.track_number},
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppException("Track data must be unique", HTTPStatus.CONFLICT) from exc
        return await self.get_track(track.id)

    async def list_tracks(self) -> list[Track]:
        return await self.academic.list_tracks()

    async def get_track(self, track_id: UUID) -> Track:
        track = await self.academic.get_track(track_id)
        if track is None:
            raise AppException("Track not found", HTTPStatus.NOT_FOUND)
        track.levels.sort(key=lambda level: level.level_number)
        return track

    async def update_track(self, track_id: UUID, payload: TrackUpdate, actor: User) -> Track:
        track = await self.get_track(track_id)
        old_value = {"code": track.code, "name": track.name, "track_number": track.track_number}
        update_data = payload.model_dump(exclude_unset=True)
        if "code" in update_data:
            existing = await self.academic.get_track_by_code(update_data["code"], include_deleted=True)
            if existing is not None and existing.id != track.id:
                raise AppException("Track code already exists", HTTPStatus.CONFLICT)
        if "name" in update_data or "track_number" in update_data:
            name = update_data.get("name", track.name)
            track_number = update_data.get("track_number", track.track_number)
            existing = await self.academic.get_track_by_name_or_number(name, track_number, True)
            if existing is not None and existing.id != track.id:
                raise AppException("Track name or number already exists", HTTPStatus.CONFLICT)
        for field, value in update_data.items():
            setattr(track, field, value)
        await self._commit_update(
            actor,
            "track",
            track.id,
            old_value,
            {"code": track.code, "name": track.name, "track_number": track.track_number},
        )
        return await self.get_track(track.id)

    async def delete_track(self, track_id: UUID, actor: User) -> None:
        track = await self.get_track(track_id)
        await self._soft_delete(track, actor, "track")

    async def create_level(self, payload: LevelCreate, actor: User | None) -> Level:
        await self._require_track(payload.track_id)
        if await self.academic.get_level_by_track_and_number(payload.track_id, payload.level_number, True) is not None:
            raise AppException("Level number already exists for this track", HTTPStatus.CONFLICT)
        level = Level(**payload.model_dump())
        return await self._create_entity(
            level,
            actor,
            "level",
            {"track_id": str(payload.track_id), "level_number": payload.level_number},
        )

    async def list_levels(self) -> list[Level]:
        return await self.academic.list_levels()

    async def get_level(self, level_id: UUID) -> Level:
        level = await self.academic.get_level(level_id)
        if level is None:
            raise AppException("Level not found", HTTPStatus.NOT_FOUND)
        return level

    async def update_level(self, level_id: UUID, payload: LevelUpdate, actor: User) -> Level:
        level = await self.get_level(level_id)
        old_value = {"track_id": str(level.track_id), "level_number": level.level_number, "title": level.title}
        update_data = payload.model_dump(exclude_unset=True)
        next_track_id = update_data.get("track_id", level.track_id)
        next_level_number = update_data.get("level_number", level.level_number)
        await self._require_track(next_track_id)
        existing = await self.academic.get_level_by_track_and_number(next_track_id, next_level_number, True)
        if existing is not None and existing.id != level.id:
            raise AppException("Level number already exists for this track", HTTPStatus.CONFLICT)
        for field, value in update_data.items():
            setattr(level, field, value)
        await self._commit_update(
            actor,
            "level",
            level.id,
            old_value,
            {"track_id": str(level.track_id), "level_number": level.level_number, "title": level.title},
        )
        return await self.get_level(level.id)

    async def delete_level(self, level_id: UUID, actor: User) -> None:
        level = await self.get_level(level_id)
        await self._soft_delete(level, actor, "level")

    async def create_class(self, payload: ClassCreate, actor: User | None) -> AcademicClass:
        if await self.academic.get_class_by_code(payload.code, include_deleted=True) is not None:
            raise AppException("Class code already exists", HTTPStatus.CONFLICT)
        await self._validate_class_payload(payload)
        academic_class = AcademicClass(**payload.model_dump())
        return await self._create_entity(
            academic_class,
            actor,
            "class",
            {"code": payload.code, "track_id": str(payload.track_id), "level_id": str(payload.level_id)},
        )

    async def list_classes_for_user(self, actor: User) -> list[AcademicClass]:
        if actor.role == UserRole.admin:
            return await self.academic.list_classes()
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            return await self.academic.list_classes_for_teacher(actor.teacher_profile.id)
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    async def list_classes_for_teacher(self, actor: User) -> list[AcademicClass]:
        if actor.role != UserRole.teacher or actor.teacher_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self.academic.list_classes_for_teacher(actor.teacher_profile.id)

    async def get_class_for_user(self, class_id: UUID, actor: User) -> AcademicClass:
        academic_class = await self.get_class(class_id)
        if actor.role == UserRole.admin:
            return academic_class
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            if actor.teacher_profile.id in {academic_class.instructor_id, academic_class.mentor_id}:
                return academic_class
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    async def get_class(self, class_id: UUID) -> AcademicClass:
        academic_class = await self.academic.get_class(class_id)
        if academic_class is None:
            raise AppException("Class not found", HTTPStatus.NOT_FOUND)
        return academic_class

    async def update_class(self, class_id: UUID, payload: ClassUpdate, actor: User) -> AcademicClass:
        academic_class = await self.get_class(class_id)
        old_value = {"code": academic_class.code, "status": academic_class.status.value}
        update_data = payload.model_dump(exclude_unset=True)
        if "code" in update_data:
            existing = await self.academic.get_class_by_code(update_data["code"], include_deleted=True)
            if existing is not None and existing.id != academic_class.id:
                raise AppException("Class code already exists", HTTPStatus.CONFLICT)
        merged_payload = ClassCreate(
            code=update_data.get("code", academic_class.code),
            branch_id=update_data.get("branch_id", academic_class.branch_id),
            cycle_id=update_data.get("cycle_id", academic_class.cycle_id),
            track_id=update_data.get("track_id", academic_class.track_id),
            level_id=update_data.get("level_id", academic_class.level_id),
            instructor_id=update_data.get("instructor_id", academic_class.instructor_id),
            mentor_id=update_data.get("mentor_id", academic_class.mentor_id),
            schedule_text=update_data.get("schedule_text", academic_class.schedule_text),
            max_students=update_data.get("max_students", academic_class.max_students),
            class_type=update_data.get("class_type", academic_class.class_type),
            start_date=update_data.get("start_date", academic_class.start_date),
            end_date=update_data.get("end_date", academic_class.end_date),
            status=update_data.get("status", academic_class.status),
        )
        await self._validate_class_payload(merged_payload)
        for field, value in update_data.items():
            setattr(academic_class, field, value)
        await self._commit_update(
            actor,
            "class",
            academic_class.id,
            old_value,
            {"code": academic_class.code, "status": academic_class.status.value},
        )
        return await self.get_class(academic_class.id)

    async def delete_class(self, class_id: UUID, actor: User) -> None:
        academic_class = await self.get_class(class_id)
        await self._soft_delete(academic_class, actor, "class")

    async def _create_entity(self, entity, actor: User | None, entity_name: str, new_value: dict):
        try:
            await self.academic.add(entity)
            await self.audit_logs.add(
                actor.id if actor else None,
                f"create_{entity_name}",
                entity_name,
                entity.id,
                new_value=new_value,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppException(f"{entity_name.title()} data must be unique", HTTPStatus.CONFLICT) from exc
        return entity

    async def _commit_update(
        self,
        actor: User,
        entity_name: str,
        entity_id: UUID,
        old_value: dict,
        new_value: dict,
    ) -> None:
        try:
            await self.audit_logs.add(actor.id, f"update_{entity_name}", entity_name, entity_id, old_value, new_value)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppException(f"{entity_name.title()} data must be unique", HTTPStatus.CONFLICT) from exc

    async def _soft_delete(self, entity, actor: User, entity_name: str) -> None:
        entity.deleted_at = datetime.now(UTC)
        await self.audit_logs.add(actor.id, f"delete_{entity_name}", entity_name, entity.id)
        await self.session.commit()

    async def _require_track(self, track_id: UUID) -> Track:
        track = await self.academic.get_track(track_id)
        if track is None:
            raise AppException("Track not found", HTTPStatus.NOT_FOUND)
        return track

    async def _create_default_levels(self, track: Track) -> None:
        for level_number in (1, 2, 3):
            self.session.add(
                Level(
                    track_id=track.id,
                    level_number=level_number,
                    title=f"{track.name} Level {level_number}",
                    duration_months=2,
                )
            )
        await self.session.flush()

    async def _validate_class_payload(self, payload: ClassCreate) -> None:
        branch = await self.academic.get_branch(payload.branch_id)
        cycle = await self.academic.get_cycle(payload.cycle_id)
        track = await self.academic.get_track(payload.track_id)
        level = await self.academic.get_level(payload.level_id)
        instructor = await self.academic.get_teacher_profile(payload.instructor_id)
        mentor = await self.academic.get_teacher_profile(payload.mentor_id)
        if branch is None:
            raise AppException("Branch not found", HTTPStatus.NOT_FOUND)
        if cycle is None:
            raise AppException("Cycle not found", HTTPStatus.NOT_FOUND)
        if track is None:
            raise AppException("Track not found", HTTPStatus.NOT_FOUND)
        if level is None:
            raise AppException("Level not found", HTTPStatus.NOT_FOUND)
        if instructor is None or mentor is None:
            raise AppException("Teacher profile not found", HTTPStatus.NOT_FOUND)
        if level.track_id != track.id:
            raise AppException("Level must belong to the selected track", HTTPStatus.BAD_REQUEST)
        if not payload.code.startswith(track.code):
            raise AppException("Class code must start with the track code", HTTPStatus.BAD_REQUEST)
        expected_type_digit = "1" if payload.class_type == ClassType.online else "5"
        if payload.code[2] != expected_type_digit:
            raise AppException("Class code type digit does not match class_type", HTTPStatus.BAD_REQUEST)
