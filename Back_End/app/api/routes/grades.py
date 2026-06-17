from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.responses import success_response
from app.db.session import get_session
from app.models.user import User
from app.schemas.grades import CorrectionCreate, CorrectionHistoryRead, GradeEntryRead
from app.services.grades import GradeService

grades_router = APIRouter()
students_router = APIRouter()
teachers_router = APIRouter()
admin_router = APIRouter()


@grades_router.get("")
async def list_grade_entries(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    entries = await GradeService(session).list_grade_entries_for_user(current_user)
    return success_response(data=[GradeEntryRead.from_model(entry).model_dump(mode="json") for entry in entries])


@grades_router.get("/{grade_entry_id}")
async def get_grade_entry(
    grade_entry_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    entry = await GradeService(session).get_grade_entry_for_user(grade_entry_id, current_user)
    return success_response(data=GradeEntryRead.from_model(entry).model_dump(mode="json"))


@grades_router.post("/{grade_entry_id}/corrections")
async def create_correction(
    grade_entry_id: UUID,
    payload: CorrectionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    correction = await GradeService(session).create_correction(grade_entry_id, payload, current_user)
    return success_response(data=GradeEntryRead.from_model(correction).model_dump(mode="json"))


@grades_router.get("/{grade_entry_id}/corrections")
async def list_corrections_for_entry(
    grade_entry_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    corrections = await GradeService(session).list_corrections_for_entry(grade_entry_id, current_user)
    return success_response(data=[GradeEntryRead.from_model(entry).model_dump(mode="json") for entry in corrections])


@students_router.get("/me/grade-entries")
async def list_my_grade_entries(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    entries = await GradeService(session).list_student_grade_entries(current_user)
    return success_response(data=[GradeEntryRead.from_model(entry).model_dump(mode="json") for entry in entries])


@teachers_router.get("/me/classes/{class_id}/grade-entries")
async def list_my_class_grade_entries(
    class_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    entries = await GradeService(session).list_teacher_class_grade_entries(class_id, current_user)
    return success_response(data=[GradeEntryRead.from_model(entry).model_dump(mode="json") for entry in entries])


@teachers_router.get("/me/corrections-history")
async def list_my_corrections_history(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    corrections = await GradeService(session).list_teacher_corrections_history(current_user)
    return success_response(data=[CorrectionHistoryRead.from_model(entry).model_dump(mode="json") for entry in corrections])


@admin_router.get("/corrections-history")
async def list_admin_corrections_history(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    corrections = await GradeService(session).list_admin_corrections_history(current_user)
    return success_response(data=[CorrectionHistoryRead.from_model(entry).model_dump(mode="json") for entry in corrections])
