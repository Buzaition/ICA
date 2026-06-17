from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.responses import success_response
from app.db.session import get_session
from app.models.user import User
from app.schemas.progress import ProgressSnapshotRead
from app.services.progress import ProgressService

students_router = APIRouter()
teachers_router = APIRouter()
progress_router = APIRouter()


@students_router.get("/me/progress")
async def get_my_progress(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    progress = await ProgressService(session).get_student_own_progress(current_user)
    return success_response(data=progress.model_dump(mode="json"))


@teachers_router.get("/me/classes/{class_id}/progress")
async def get_my_class_progress(
    class_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    progress = await ProgressService(session).get_class_progress_for_user(class_id, current_user)
    return success_response(data=progress.model_dump(mode="json"))


@teachers_router.post("/me/classes/{class_id}/progress-snapshots")
async def create_my_class_progress_snapshots(
    class_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    snapshots = await ProgressService(session).create_snapshots_for_class(class_id, current_user)
    return success_response(data=[ProgressSnapshotRead.from_model(snapshot).model_dump(mode="json") for snapshot in snapshots])


@progress_router.get("/students/{student_id}")
async def get_student_progress(
    student_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    progress = await ProgressService(session).get_student_progress_admin(student_id, current_user)
    return success_response(data=progress.model_dump(mode="json"))


@progress_router.get("/classes/{class_id}")
async def get_class_progress(
    class_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    progress = await ProgressService(session).get_class_progress_for_user(class_id, current_user)
    return success_response(data=progress.model_dump(mode="json"))


@progress_router.get("/classes/{class_id}/snapshots")
async def list_class_progress_snapshots(
    class_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    snapshots = await ProgressService(session).list_snapshots_for_class(class_id, current_user)
    return success_response(data=[ProgressSnapshotRead.from_model(snapshot).model_dump(mode="json") for snapshot in snapshots])


@progress_router.post("/classes/{class_id}/snapshots")
async def create_class_progress_snapshots(
    class_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    snapshots = await ProgressService(session).create_snapshots_for_class(class_id, current_user)
    return success_response(data=[ProgressSnapshotRead.from_model(snapshot).model_dump(mode="json") for snapshot in snapshots])


@progress_router.get("/teachers/{teacher_id}")
async def get_teacher_progress(
    teacher_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    progress = await ProgressService(session).get_teacher_progress(teacher_id, current_user)
    return success_response(data=progress.model_dump(mode="json"))
