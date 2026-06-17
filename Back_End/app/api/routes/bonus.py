from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.responses import success_response
from app.db.session import get_session
from app.models.user import User
from app.schemas.bonus import BonusCreate, BonusRead
from app.services.bonus import BonusService

bonus_router = APIRouter()
students_router = APIRouter()
teachers_router = APIRouter()


@bonus_router.post("")
async def create_bonus(
    payload: BonusCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    grade_entry, weekly_count, weekly_remaining = await BonusService(session).create_bonus(payload, current_user)
    return success_response(data=BonusRead.from_model(grade_entry, weekly_count, weekly_remaining).model_dump(mode="json"))


@bonus_router.get("")
async def list_bonus(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = BonusService(session)
    entries = await service.list_bonus_for_user(current_user)
    counts = await service.weekly_counts_for_entries(entries)
    return success_response(
        data=[
            BonusRead.from_model(entry, counts[entry.id][0], counts[entry.id][1]).model_dump(mode="json")
            for entry in entries
        ]
    )


@students_router.get("/me/bonus")
async def list_my_bonus(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = BonusService(session)
    entries = await service.list_student_bonus(current_user)
    counts = await service.weekly_counts_for_entries(entries)
    return success_response(
        data=[
            BonusRead.from_model(entry, counts[entry.id][0], counts[entry.id][1]).model_dump(mode="json")
            for entry in entries
        ]
    )


@teachers_router.get("/me/classes/{class_id}/bonus")
async def list_my_class_bonus(
    class_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = BonusService(session)
    entries = await service.list_teacher_class_bonus(class_id, current_user)
    counts = await service.weekly_counts_for_entries(entries)
    return success_response(
        data=[
            BonusRead.from_model(entry, counts[entry.id][0], counts[entry.id][1]).model_dump(mode="json")
            for entry in entries
        ]
    )
