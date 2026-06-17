from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.responses import success_response
from app.db.session import get_session
from app.models.user import User
from app.schemas.quizzes import ManualQuizCreate, QuizRead, QuizResultRead, QuizResultUpdate, QuizSubmissionResultRead
from app.services.quizzes import QuizService, QuizSubmissionResult

quizzes_router = APIRouter()
quiz_results_router = APIRouter()
teachers_router = APIRouter()
students_router = APIRouter()


@quizzes_router.post("/manual")
async def create_manual_quiz(
    payload: ManualQuizCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await QuizService(session).submit_manual_quiz(payload, current_user)
    return success_response(data=_result_payload(result))


@quizzes_router.post("/upload-csv")
async def upload_quiz_csv(
    class_id: UUID = Form(...),
    title: str = Form(...),
    quiz_date: date = Form(...),
    max_grade: float = Form(...),
    description: str | None = Form(default=None),
    teacher_id: UUID | None = Form(default=None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await QuizService(session).upload_csv_quiz(
        class_id,
        teacher_id,
        title,
        description,
        quiz_date,
        max_grade,
        file,
        current_user,
    )
    return success_response(data=_result_payload(result))


@quizzes_router.get("")
async def list_quizzes(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    quizzes = await QuizService(session).list_quizzes_for_user(current_user)
    return success_response(data=[QuizRead.from_model(quiz).model_dump(mode="json") for quiz in quizzes])


@quizzes_router.get("/{quiz_id}")
async def get_quiz(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    quiz = await QuizService(session).get_quiz_for_user(quiz_id, current_user)
    return success_response(data=QuizRead.from_model(quiz).model_dump(mode="json"))


@quizzes_router.get("/{quiz_id}/results")
async def list_quiz_results(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    results = await QuizService(session).list_results_for_quiz(quiz_id, current_user)
    return success_response(data=[QuizResultRead.from_model(result).model_dump(mode="json") for result in results])


@quiz_results_router.put("/{result_id}")
async def update_quiz_result(
    result_id: UUID,
    payload: QuizResultUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await QuizService(session).update_result(result_id, payload, current_user)
    return success_response(data=QuizResultRead.from_model(result).model_dump(mode="json"))


@quiz_results_router.get("")
async def list_quiz_results_admin(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    results = await QuizService(session).list_all_results_for_admin(current_user)
    return success_response(data=[QuizResultRead.from_model(result).model_dump(mode="json") for result in results])


@teachers_router.get("/me/classes/{class_id}/quizzes")
async def list_my_class_quizzes(
    class_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    quizzes = await QuizService(session).list_teacher_class_quizzes(class_id, current_user)
    return success_response(data=[QuizRead.from_model(quiz).model_dump(mode="json") for quiz in quizzes])


@students_router.get("/me/quizzes")
async def list_my_quizzes(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    results = await QuizService(session).list_student_quiz_results(current_user)
    return success_response(data=[QuizResultRead.from_model(result).model_dump(mode="json") for result in results])


def _result_payload(result: QuizSubmissionResult) -> dict:
    return QuizSubmissionResultRead(
        quiz_id=result.quiz.id,
        total_rows=result.total_rows,
        success_count=result.success_count,
        error_count=result.error_count,
        errors=result.errors,
        quiz=QuizRead.from_model(result.quiz),
        results=[QuizResultRead.from_model(item) for item in result.results],
    ).model_dump(mode="json")
