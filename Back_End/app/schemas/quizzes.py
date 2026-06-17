from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import QuizSourceType
from app.models.quiz import Quiz, QuizResult


class ManualQuizResultCreate(BaseModel):
    student_id: UUID
    earned_grade: float = Field(ge=0)
    student_code: str | None = None
    row_number: int | None = None


class ManualQuizCreate(BaseModel):
    class_id: UUID
    teacher_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    quiz_date: date
    max_grade: float = Field(gt=0)
    results: list[ManualQuizResultCreate] = Field(min_length=1)


class QuizResultUpdate(BaseModel):
    earned_grade: float = Field(ge=0)


class QuizUploadErrorRead(BaseModel):
    row_number: int
    student_code: str | None
    reason: str


class QuizRead(BaseModel):
    id: UUID
    class_id: UUID
    class_code: str
    teacher_id: UUID
    teacher_name: str
    title: str
    description: str | None
    quiz_date: date
    max_grade: float
    source_type: QuizSourceType
    created_at: datetime

    @classmethod
    def from_model(cls, quiz: Quiz) -> "QuizRead":
        return cls(
            id=quiz.id,
            class_id=quiz.class_id,
            class_code=quiz.academic_class.code,
            teacher_id=quiz.teacher_id,
            teacher_name=quiz.teacher.full_name,
            title=quiz.title,
            description=quiz.description,
            quiz_date=quiz.quiz_date,
            max_grade=float(quiz.max_grade),
            source_type=quiz.source_type,
            created_at=quiz.created_at,
        )


class QuizResultRead(BaseModel):
    id: UUID
    quiz_id: UUID
    student_id: UUID
    student_code: str
    student_name: str
    earned_grade: float
    max_grade: float
    grade_entry_id: UUID | None

    @classmethod
    def from_model(cls, result: QuizResult) -> "QuizResultRead":
        return cls(
            id=result.id,
            quiz_id=result.quiz_id,
            student_id=result.student_id,
            student_code=result.student.student_code,
            student_name=result.student.full_name,
            earned_grade=float(result.earned_grade),
            max_grade=float(result.max_grade),
            grade_entry_id=result.grade_entry_id,
        )


class QuizSubmissionResultRead(BaseModel):
    quiz_id: UUID
    total_rows: int
    success_count: int
    error_count: int
    errors: list[QuizUploadErrorRead]
    quiz: QuizRead
    results: list[QuizResultRead]
