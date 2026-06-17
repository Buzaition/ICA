from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.responses import success_response
from app.db.session import get_session
from app.models.user import User
from app.services.ranking import RankingService

students_router = APIRouter()
teachers_router = APIRouter()
ranking_router = APIRouter()


@students_router.get("/me/ranking/top3")
async def get_my_class_top3_ranking(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    ranking = await RankingService(session).get_student_top3(current_user)
    return success_response(data=[item.model_dump(mode="json") for item in ranking])


@teachers_router.get("/me/classes/{class_id}/ranking")
async def get_my_class_ranking(
    class_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    ranking = await RankingService(session).get_teacher_class_ranking(class_id, current_user)
    return success_response(data=[item.model_dump(mode="json") for item in ranking])


@ranking_router.get("/classes/{class_id}")
async def get_class_ranking(
    class_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    ranking = await RankingService(session).get_admin_class_ranking(class_id, current_user)
    return success_response(data=[item.model_dump(mode="json") for item in ranking])


@ranking_router.get("/tracks/{track_id}")
async def get_track_ranking(
    track_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    ranking = await RankingService(session).get_admin_track_ranking(track_id, current_user)
    return success_response(data=[item.model_dump(mode="json") for item in ranking])
