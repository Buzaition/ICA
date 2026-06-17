from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.responses import success_response
from app.db.session import get_session
from app.models.user import User
from app.schemas.final_projects import FinalProjectRead, FinalProjectReview, FinalProjectSubmit
from app.services.final_projects import FinalProjectService

students_router = APIRouter()
teachers_router = APIRouter()
final_projects_router = APIRouter()


@students_router.post("/me/final-project")
async def submit_my_final_project(
    payload: FinalProjectSubmit,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    final_project = await FinalProjectService(session).submit_own_project(payload, current_user)
    return success_response(data=FinalProjectRead.from_model(final_project).model_dump(mode="json"))


@students_router.get("/me/final-project")
async def get_my_final_project(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    final_project = await FinalProjectService(session).get_own_project(current_user)
    return success_response(data=FinalProjectRead.from_model(final_project).model_dump(mode="json"))


@students_router.put("/me/final-project")
async def update_my_final_project(
    payload: FinalProjectSubmit,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    final_project = await FinalProjectService(session).update_own_project(payload, current_user)
    return success_response(data=FinalProjectRead.from_model(final_project).model_dump(mode="json"))


@teachers_router.get("/me/classes/{class_id}/final-projects")
async def list_my_class_final_projects(
    class_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    final_projects = await FinalProjectService(session).list_for_teacher_class(class_id, current_user)
    return success_response(data=[FinalProjectRead.from_model(item).model_dump(mode="json") for item in final_projects])


@final_projects_router.get("")
async def list_final_projects(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    final_projects = await FinalProjectService(session).list_all_for_admin(current_user)
    return success_response(data=[FinalProjectRead.from_model(item).model_dump(mode="json") for item in final_projects])


@final_projects_router.get("/{final_project_id}")
async def get_final_project(
    final_project_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    final_project = await FinalProjectService(session).get_for_admin(final_project_id, current_user)
    return success_response(data=FinalProjectRead.from_model(final_project).model_dump(mode="json"))


@final_projects_router.post("/{final_project_id}/review")
async def review_final_project(
    final_project_id: UUID,
    payload: FinalProjectReview,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    final_project = await FinalProjectService(session).review_project(final_project_id, payload, current_user)
    return success_response(data=FinalProjectRead.from_model(final_project).model_dump(mode="json"))
