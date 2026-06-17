from datetime import date
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.academic import Class as AcademicClass
from app.models.profiles import StudentProfile
from app.models.quiz import Quiz, QuizResult


class QuizRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_quiz(self, quiz: Quiz) -> Quiz:
        self.session.add(quiz)
        await self.session.flush()
        await self.session.refresh(quiz)
        return quiz

    async def add_result(self, result: QuizResult) -> QuizResult:
        self.session.add(result)
        await self.session.flush()
        await self.session.refresh(result)
        return result

    async def get_quiz_by_identity(self, class_id: UUID, teacher_id: UUID, title: str, quiz_date: date) -> Quiz | None:
        return await self.session.scalar(
            self._quiz_query().where(
                Quiz.class_id == class_id,
                Quiz.teacher_id == teacher_id,
                Quiz.title == title,
                Quiz.quiz_date == quiz_date,
                Quiz.deleted_at.is_(None),
            )
        )

    async def get_quiz_by_id(self, quiz_id: UUID, include_deleted: bool = False) -> Quiz | None:
        statement = self._quiz_query().where(Quiz.id == quiz_id)
        if not include_deleted:
            statement = statement.where(Quiz.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def list_quizzes(self) -> list[Quiz]:
        result = await self.session.scalars(self._quiz_query().where(Quiz.deleted_at.is_(None)).order_by(Quiz.quiz_date.desc()))
        return list(result.all())

    async def list_quizzes_for_class(self, class_id: UUID) -> list[Quiz]:
        result = await self.session.scalars(
            self._quiz_query().where(Quiz.class_id == class_id, Quiz.deleted_at.is_(None)).order_by(Quiz.quiz_date.desc())
        )
        return list(result.all())

    async def list_quizzes_for_teacher(self, teacher_profile_id: UUID) -> list[Quiz]:
        result = await self.session.scalars(
            self._quiz_query()
            .join(Quiz.academic_class)
            .where(
                Quiz.deleted_at.is_(None),
                or_(AcademicClass.instructor_id == teacher_profile_id, AcademicClass.mentor_id == teacher_profile_id),
            )
            .order_by(Quiz.quiz_date.desc())
        )
        return list(result.all())

    async def get_result_by_id(self, result_id: UUID, include_deleted: bool = False) -> QuizResult | None:
        statement = self._result_query().where(QuizResult.id == result_id)
        if not include_deleted:
            statement = statement.where(QuizResult.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def get_result_for_quiz_student(self, quiz_id: UUID, student_id: UUID) -> QuizResult | None:
        return await self.session.scalar(
            self._result_query().where(
                QuizResult.quiz_id == quiz_id,
                QuizResult.student_id == student_id,
                QuizResult.deleted_at.is_(None),
            )
        )

    async def list_results_for_quiz(self, quiz_id: UUID) -> list[QuizResult]:
        result = await self.session.scalars(
            self._result_query().where(QuizResult.quiz_id == quiz_id, QuizResult.deleted_at.is_(None)).order_by(QuizResult.created_at)
        )
        return list(result.all())

    async def list_results_for_student(self, student_id: UUID) -> list[QuizResult]:
        result = await self.session.scalars(
            self._result_query()
            .join(QuizResult.quiz)
            .where(QuizResult.student_id == student_id, QuizResult.deleted_at.is_(None), Quiz.deleted_at.is_(None))
            .order_by(Quiz.quiz_date.desc())
        )
        return list(result.all())

    async def list_results_all(self) -> list[QuizResult]:
        result = await self.session.scalars(
            self._result_query()
            .join(QuizResult.quiz)
            .where(QuizResult.deleted_at.is_(None), Quiz.deleted_at.is_(None))
            .order_by(Quiz.quiz_date.desc())
        )
        return list(result.all())

    def _quiz_query(self):
        return select(Quiz).options(
            selectinload(Quiz.academic_class).selectinload(AcademicClass.branch),
            selectinload(Quiz.academic_class).selectinload(AcademicClass.cycle),
            selectinload(Quiz.academic_class).selectinload(AcademicClass.track),
            selectinload(Quiz.academic_class).selectinload(AcademicClass.level),
            selectinload(Quiz.teacher),
            selectinload(Quiz.created_by_user),
        )

    def _result_query(self):
        return select(QuizResult).options(
            selectinload(QuizResult.quiz).selectinload(Quiz.academic_class),
            selectinload(QuizResult.quiz).selectinload(Quiz.teacher),
            selectinload(QuizResult.student).selectinload(StudentProfile.user),
            selectinload(QuizResult.grade_entry),
        )
