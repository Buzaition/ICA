from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.responses import success_response
from app.db.session import get_session
from app.domain.enums import UserRole
from app.models.user import User
from app.schemas.academic import (
    BranchCreate,
    BranchRead,
    BranchUpdate,
    ClassCreate,
    ClassRead,
    ClassUpdate,
    CycleCreate,
    CycleRead,
    CycleUpdate,
    LevelCreate,
    LevelRead,
    LevelUpdate,
    TrackCreate,
    TrackRead,
    TrackUpdate,
)
from app.services.academic import AcademicService

branches_router = APIRouter()
cycles_router = APIRouter()
tracks_router = APIRouter()
levels_router = APIRouter()
classes_router = APIRouter()
teachers_router = APIRouter()


@branches_router.post("")
async def create_branch(
    payload: BranchCreate,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    branch = await AcademicService(session).create_branch(payload, current_user)
    return success_response(data=BranchRead.model_validate(branch).model_dump(mode="json"))


@branches_router.get("")
async def list_branches(
    _: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    branches = await AcademicService(session).list_branches()
    return success_response(data=[BranchRead.model_validate(branch).model_dump(mode="json") for branch in branches])


@branches_router.get("/{branch_id}")
async def get_branch(
    branch_id: UUID,
    _: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    branch = await AcademicService(session).get_branch(branch_id)
    return success_response(data=BranchRead.model_validate(branch).model_dump(mode="json"))


@branches_router.put("/{branch_id}")
async def update_branch(
    branch_id: UUID,
    payload: BranchUpdate,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    branch = await AcademicService(session).update_branch(branch_id, payload, current_user)
    return success_response(data=BranchRead.model_validate(branch).model_dump(mode="json"))


@branches_router.delete("/{branch_id}")
async def delete_branch(
    branch_id: UUID,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await AcademicService(session).delete_branch(branch_id, current_user)
    return success_response()


@cycles_router.post("")
async def create_cycle(
    payload: CycleCreate,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    cycle = await AcademicService(session).create_cycle(payload, current_user)
    return success_response(data=CycleRead.model_validate(cycle).model_dump(mode="json"))


@cycles_router.get("")
async def list_cycles(
    _: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    cycles = await AcademicService(session).list_cycles()
    return success_response(data=[CycleRead.model_validate(cycle).model_dump(mode="json") for cycle in cycles])


@cycles_router.get("/{cycle_id}")
async def get_cycle(
    cycle_id: UUID,
    _: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    cycle = await AcademicService(session).get_cycle(cycle_id)
    return success_response(data=CycleRead.model_validate(cycle).model_dump(mode="json"))


@cycles_router.put("/{cycle_id}")
async def update_cycle(
    cycle_id: UUID,
    payload: CycleUpdate,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    cycle = await AcademicService(session).update_cycle(cycle_id, payload, current_user)
    return success_response(data=CycleRead.model_validate(cycle).model_dump(mode="json"))


@cycles_router.delete("/{cycle_id}")
async def delete_cycle(
    cycle_id: UUID,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await AcademicService(session).delete_cycle(cycle_id, current_user)
    return success_response()


@tracks_router.post("")
async def create_track(
    payload: TrackCreate,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    track = await AcademicService(session).create_track(payload, current_user)
    return success_response(data=TrackRead.model_validate(track).model_dump(mode="json"))


@tracks_router.get("")
async def list_tracks(
    _: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    tracks = await AcademicService(session).list_tracks()
    return success_response(data=[TrackRead.model_validate(track).model_dump(mode="json") for track in tracks])


@tracks_router.get("/{track_id}")
async def get_track(
    track_id: UUID,
    _: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    track = await AcademicService(session).get_track(track_id)
    return success_response(data=TrackRead.model_validate(track).model_dump(mode="json"))


@tracks_router.put("/{track_id}")
async def update_track(
    track_id: UUID,
    payload: TrackUpdate,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    track = await AcademicService(session).update_track(track_id, payload, current_user)
    return success_response(data=TrackRead.model_validate(track).model_dump(mode="json"))


@tracks_router.delete("/{track_id}")
async def delete_track(
    track_id: UUID,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await AcademicService(session).delete_track(track_id, current_user)
    return success_response()


@levels_router.post("")
async def create_level(
    payload: LevelCreate,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    level = await AcademicService(session).create_level(payload, current_user)
    return success_response(data=LevelRead.model_validate(level).model_dump(mode="json"))


@levels_router.get("")
async def list_levels(
    _: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    levels = await AcademicService(session).list_levels()
    return success_response(data=[LevelRead.model_validate(level).model_dump(mode="json") for level in levels])


@levels_router.get("/{level_id}")
async def get_level(
    level_id: UUID,
    _: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    level = await AcademicService(session).get_level(level_id)
    return success_response(data=LevelRead.model_validate(level).model_dump(mode="json"))


@levels_router.put("/{level_id}")
async def update_level(
    level_id: UUID,
    payload: LevelUpdate,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    level = await AcademicService(session).update_level(level_id, payload, current_user)
    return success_response(data=LevelRead.model_validate(level).model_dump(mode="json"))


@levels_router.delete("/{level_id}")
async def delete_level(
    level_id: UUID,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await AcademicService(session).delete_level(level_id, current_user)
    return success_response()


@classes_router.post("")
async def create_class(
    payload: ClassCreate,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    academic_class = await AcademicService(session).create_class(payload, current_user)
    return success_response(data=ClassRead.model_validate(academic_class).model_dump(mode="json"))


@classes_router.get("")
async def list_classes(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    classes = await AcademicService(session).list_classes_for_user(current_user)
    return success_response(data=[ClassRead.model_validate(item).model_dump(mode="json") for item in classes])


@classes_router.get("/{class_id}")
async def get_class(
    class_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    academic_class = await AcademicService(session).get_class_for_user(class_id, current_user)
    return success_response(data=ClassRead.model_validate(academic_class).model_dump(mode="json"))


@classes_router.put("/{class_id}")
async def update_class(
    class_id: UUID,
    payload: ClassUpdate,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    academic_class = await AcademicService(session).update_class(class_id, payload, current_user)
    return success_response(data=ClassRead.model_validate(academic_class).model_dump(mode="json"))


@classes_router.delete("/{class_id}")
async def delete_class(
    class_id: UUID,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await AcademicService(session).delete_class(class_id, current_user)
    return success_response()


@teachers_router.get("/me/classes")
async def get_my_classes(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    classes = await AcademicService(session).list_classes_for_teacher(current_user)
    return success_response(data=[ClassRead.model_validate(item).model_dump(mode="json") for item in classes])
