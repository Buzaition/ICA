from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.responses import success_response
from app.db.session import get_session
from app.domain.enums import AttendanceSessionType
from app.models.user import User
from app.schemas.attendance import (
    AttendanceRecordRead,
    AttendanceRecordUpdate,
    AttendanceSessionRead,
    AttendanceSubmissionResultRead,
    ManualAttendanceCreate,
)
from app.services.attendance import AttendanceService, AttendanceSubmissionResult

attendance_router = APIRouter()
teachers_router = APIRouter()
students_router = APIRouter()


@attendance_router.post("/manual")
async def create_manual_attendance(
    payload: ManualAttendanceCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await AttendanceService(session).submit_manual_attendance(payload, current_user)
    return success_response(data=_result_payload(result))


@attendance_router.post("/upload-csv")
async def upload_attendance_csv(
    class_id: UUID = Form(...),
    session_type: AttendanceSessionType = Form(...),
    session_date: date = Form(...),
    teacher_id: UUID | None = Form(default=None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await AttendanceService(session).upload_csv_attendance(
        class_id,
        teacher_id,
        session_type,
        session_date,
        file,
        current_user,
    )
    return success_response(data=_result_payload(result))


@attendance_router.get("/sessions")
async def list_attendance_sessions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    sessions = await AttendanceService(session).list_sessions_for_user(current_user)
    return success_response(data=[AttendanceSessionRead.from_model(item).model_dump(mode="json") for item in sessions])


@attendance_router.get("/sessions/{session_id}")
async def get_attendance_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    attendance_session = await AttendanceService(session).get_session_for_user(session_id, current_user)
    return success_response(data=AttendanceSessionRead.from_model(attendance_session).model_dump(mode="json"))


@attendance_router.get("/sessions/{session_id}/records")
async def list_attendance_session_records(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    records = await AttendanceService(session).list_records_for_session(session_id, current_user)
    return success_response(data=[AttendanceRecordRead.from_model(item).model_dump(mode="json") for item in records])


@attendance_router.put("/records/{record_id}")
async def update_attendance_record(
    record_id: UUID,
    payload: AttendanceRecordUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    record = await AttendanceService(session).update_record(record_id, payload, current_user)
    return success_response(data=AttendanceRecordRead.from_model(record).model_dump(mode="json"))


@attendance_router.get("")
async def list_all_attendance(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    records = await AttendanceService(session).list_all_records_for_admin(current_user)
    return success_response(data=[AttendanceRecordRead.from_model(item).model_dump(mode="json") for item in records])


@teachers_router.get("/me/classes/{class_id}/attendance")
async def list_my_class_attendance(
    class_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    sessions = await AttendanceService(session).list_teacher_class_attendance(class_id, current_user)
    return success_response(data=[AttendanceSessionRead.from_model(item).model_dump(mode="json") for item in sessions])


@students_router.get("/me/attendance")
async def list_my_attendance(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    records = await AttendanceService(session).list_student_attendance(current_user)
    return success_response(data=[AttendanceRecordRead.from_model(item).model_dump(mode="json") for item in records])


def _result_payload(result: AttendanceSubmissionResult) -> dict:
    return AttendanceSubmissionResultRead(
        created_session_id=result.session.id,
        total_rows=result.total_rows,
        success_count=result.success_count,
        error_count=result.error_count,
        errors=result.errors,
        session=AttendanceSessionRead.from_model(result.session),
        records=[AttendanceRecordRead.from_model(item) for item in result.records],
    ).model_dump(mode="json")
