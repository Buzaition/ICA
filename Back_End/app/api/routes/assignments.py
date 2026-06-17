from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.responses import success_response
from app.db.session import get_session
from app.domain.enums import UserRole
from app.models.user import User
from app.schemas.assignments import (
    AdminSubmissionReview,
    AssignmentCreate,
    AssignmentRead,
    AssignmentUpdate,
    PendingSubmissionRead,
    ReviewedSubmissionRead,
    SubmissionCreate,
    SubmissionRead,
    SubmissionReject,
)
from app.services.assignments import AssignmentService

assignments_router = APIRouter()
students_router = APIRouter()
teachers_router = APIRouter()
submissions_router = APIRouter()


@assignments_router.post("")
async def create_assignment(
    payload: AssignmentCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    assignment = await AssignmentService(session).create_assignment(payload, current_user)
    return success_response(data=AssignmentRead.from_model(assignment).model_dump(mode="json"))


@assignments_router.get("")
async def list_assignments(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    assignments = await AssignmentService(session).list_assignments_for_user(current_user)
    return success_response(data=[AssignmentRead.from_model(item).model_dump(mode="json") for item in assignments])


@assignments_router.get("/{assignment_id}")
async def get_assignment(
    assignment_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    assignment = await AssignmentService(session).get_assignment_for_user(assignment_id, current_user)
    return success_response(data=AssignmentRead.from_model(assignment).model_dump(mode="json"))


@assignments_router.put("/{assignment_id}")
async def update_assignment(
    assignment_id: UUID,
    payload: AssignmentUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    assignment = await AssignmentService(session).update_assignment(assignment_id, payload, current_user)
    return success_response(data=AssignmentRead.from_model(assignment).model_dump(mode="json"))


@assignments_router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await AssignmentService(session).delete_assignment(assignment_id, current_user)
    return success_response()


@assignments_router.post("/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: UUID,
    payload: SubmissionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    submission = await AssignmentService(session).submit_assignment(assignment_id, payload, current_user)
    return success_response(data=SubmissionRead.from_model(submission).model_dump(mode="json"))


@students_router.get("/me/assignments")
async def list_my_assignments(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    assignments = await AssignmentService(session).list_student_assignments(current_user)
    return success_response(data=[AssignmentRead.from_model(item).model_dump(mode="json") for item in assignments])


@students_router.get("/me/submissions")
async def list_my_submissions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    submissions = await AssignmentService(session).list_student_submissions(current_user)
    return success_response(data=[SubmissionRead.from_model(item).model_dump(mode="json") for item in submissions])


@teachers_router.get("/me/classes/{class_id}/assignments")
async def list_my_class_assignments(
    class_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    assignments = await AssignmentService(session).list_teacher_class_assignments(class_id, current_user)
    return success_response(data=[AssignmentRead.from_model(item).model_dump(mode="json") for item in assignments])


@teachers_router.get("/me/assignments/pending")
async def list_pending_assignments(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    submissions = await AssignmentService(session).list_pending_for_teacher(current_user)
    return success_response(data=[PendingSubmissionRead.from_model(item).model_dump(mode="json") for item in submissions])


@teachers_router.get("/me/assignments/reviewed")
async def list_reviewed_assignments(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    submissions = await AssignmentService(session).list_reviewed_for_teacher(current_user)
    return success_response(data=[ReviewedSubmissionRead.from_model(item).model_dump(mode="json") for item in submissions])


@teachers_router.get("/me/assignments/late")
async def list_late_assignments(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    submissions = await AssignmentService(session).list_late_for_teacher(current_user)
    return success_response(data=[PendingSubmissionRead.from_model(item).model_dump(mode="json") for item in submissions])


@submissions_router.post("/{submission_id}/review")
async def review_submission(
    submission_id: UUID,
    payload: AdminSubmissionReview,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    submission = await AssignmentService(session).review_submission(submission_id, payload, current_user)
    return success_response(data=SubmissionRead.from_model(submission).model_dump(mode="json"))


@submissions_router.post("/{submission_id}/reject")
async def reject_submission(
    submission_id: UUID,
    payload: SubmissionReject,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    submission = await AssignmentService(session).reject_submission(submission_id, payload, current_user)
    return success_response(data=SubmissionRead.from_model(submission).model_dump(mode="json"))


@submissions_router.get("")
async def list_submissions(
    _: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    submissions = await AssignmentService(session).list_admin_submissions()
    return success_response(data=[SubmissionRead.from_model(item).model_dump(mode="json") for item in submissions])


@submissions_router.get("/{submission_id}")
async def get_submission(
    submission_id: UUID,
    _: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    submission = await AssignmentService(session).get_submission_for_admin(submission_id)
    return success_response(data=SubmissionRead.from_model(submission).model_dump(mode="json"))
