from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.responses import success_response
from app.db.session import get_session
from app.models.user import User
from app.services.dashboards import DashboardService

admin_router = APIRouter()
teachers_router = APIRouter()
students_router = APIRouter()


@admin_router.get("/dashboard")
async def get_admin_dashboard(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    dashboard = await DashboardService(session).get_admin_dashboard(current_user)
    return success_response(data=dashboard.model_dump(mode="json"))


@teachers_router.get("/me/dashboard")
async def get_teacher_dashboard(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    dashboard = await DashboardService(session).get_teacher_dashboard(current_user)
    return success_response(data=dashboard.model_dump(mode="json"))


@students_router.get("/me/dashboard")
async def get_student_dashboard(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    dashboard = await DashboardService(session).get_student_dashboard(current_user)
    return success_response(data=dashboard.model_dump(mode="json"))
