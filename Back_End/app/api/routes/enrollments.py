from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.responses import success_response
from app.db.session import get_session
from app.domain.enums import UserRole
from app.models.user import User
from app.schemas.enrollments import EnrollmentCreate, EnrollmentRead, TeacherClassStudentRead
from app.services.enrollments import EnrollmentService

enrollments_router = APIRouter()
teacher_students_router = APIRouter()
student_class_router = APIRouter()


@enrollments_router.post("")
async def create_enrollment(
    payload: EnrollmentCreate,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    enrollment = await EnrollmentService(session).create_enrollment(payload, current_user)
    return success_response(data=EnrollmentRead.from_model(enrollment).model_dump(mode="json"))


@enrollments_router.get("")
async def list_enrollments(
    _: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    enrollments = await EnrollmentService(session).list_enrollments()
    return success_response(data=[EnrollmentRead.from_model(item).model_dump(mode="json") for item in enrollments])


@enrollments_router.get("/{enrollment_id}")
async def get_enrollment(
    enrollment_id: UUID,
    _: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    enrollment = await EnrollmentService(session).get_enrollment(enrollment_id)
    return success_response(data=EnrollmentRead.from_model(enrollment).model_dump(mode="json"))


@enrollments_router.delete("/{enrollment_id}")
async def remove_enrollment(
    enrollment_id: UUID,
    current_user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await EnrollmentService(session).remove_enrollment(enrollment_id, current_user)
    return success_response()


@teacher_students_router.get("/me/classes/{class_id}/students")
async def list_my_class_students(
    class_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    enrollments = await EnrollmentService(session).list_students_for_teacher_class(class_id, current_user)
    return success_response(data=[TeacherClassStudentRead.from_model(item).model_dump(mode="json") for item in enrollments])


@student_class_router.get("/me/class")
async def get_my_active_class(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    enrollment = await EnrollmentService(session).get_student_active_class(current_user)
    return success_response(data=EnrollmentRead.from_model(enrollment).model_dump(mode="json"))
