import csv
from dataclasses import dataclass
from http import HTTPStatus
from io import StringIO
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.domain.enums import EnrollmentStatus, GradeCategory, GradeSourceType, QuizSourceType, StudentStatus, UserRole
from app.models.grade import GradeEntry
from app.models.profiles import StudentProfile
from app.models.quiz import Quiz, QuizResult
from app.models.user import User
from app.repositories.academic import AcademicRepository
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.enrollments import EnrollmentRepository
from app.repositories.grades import GradeRepository
from app.repositories.quizzes import QuizRepository
from app.schemas.quizzes import ManualQuizCreate, ManualQuizResultCreate, QuizResultUpdate, QuizUploadErrorRead


@dataclass
class QuizSubmissionResult:
    quiz: Quiz
    results: list[QuizResult]
    total_rows: int
    errors: list[QuizUploadErrorRead]

    @property
    def success_count(self) -> int:
        return len(self.results)

    @property
    def error_count(self) -> int:
        return len(self.errors)


class QuizService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.academic = AcademicRepository(session)
        self.audit_logs = AuditLogRepository(session)
        self.enrollments = EnrollmentRepository(session)
        self.grades = GradeRepository(session)
        self.quizzes = QuizRepository(session)

    async def submit_manual_quiz(self, payload: ManualQuizCreate, actor: User) -> QuizSubmissionResult:
        academic_class = await self._require_class(payload.class_id)
        teacher_id = await self._resolve_teacher_id(actor, academic_class, payload.teacher_id)
        quiz = await self._get_or_create_quiz(
            payload.class_id,
            teacher_id,
            payload.title,
            payload.description,
            payload.quiz_date,
            payload.max_grade,
            QuizSourceType.manual,
            actor,
        )
        errors: list[QuizUploadErrorRead] = []
        results = await self._process_results(quiz, payload.results, QuizSourceType.manual, actor, errors)
        await self.session.commit()
        refreshed = await self._refresh_result(quiz.id, results)
        return QuizSubmissionResult(refreshed["quiz"], refreshed["results"], len(payload.results), errors)

    async def upload_csv_quiz(
        self,
        class_id: UUID,
        teacher_id: UUID | None,
        title: str,
        description: str | None,
        quiz_date,
        max_grade: float,
        file: UploadFile,
        actor: User,
    ) -> QuizSubmissionResult:
        if max_grade <= 0:
            raise AppException("Quiz max_grade must be greater than 0", HTTPStatus.BAD_REQUEST)
        academic_class = await self._require_class(class_id)
        resolved_teacher_id = await self._resolve_teacher_id(actor, academic_class, teacher_id)
        quiz = await self._get_or_create_quiz(
            class_id,
            resolved_teacher_id,
            title,
            description,
            quiz_date,
            max_grade,
            QuizSourceType.csv_upload,
            actor,
        )
        rows, errors, total_rows = await self._parse_csv(file, float(quiz.max_grade))
        results = await self._process_results(quiz, rows, QuizSourceType.csv_upload, actor, errors)
        await self.audit_logs.add(
            actor.id,
            "upload_quiz_csv",
            "quiz",
            quiz.id,
            new_value={"total_rows": total_rows, "success_count": len(results), "error_count": len(errors)},
        )
        await self.session.commit()
        refreshed = await self._refresh_result(quiz.id, results)
        return QuizSubmissionResult(refreshed["quiz"], refreshed["results"], total_rows, errors)

    async def list_quizzes_for_user(self, actor: User) -> list[Quiz]:
        if actor.role == UserRole.admin:
            return await self.quizzes.list_quizzes()
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            return await self.quizzes.list_quizzes_for_teacher(actor.teacher_profile.id)
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    async def get_quiz_for_user(self, quiz_id: UUID, actor: User) -> Quiz:
        quiz = await self._require_quiz(quiz_id)
        self._ensure_can_view_quiz(quiz, actor)
        return quiz

    async def list_results_for_quiz(self, quiz_id: UUID, actor: User) -> list[QuizResult]:
        quiz = await self._require_quiz(quiz_id)
        self._ensure_can_view_quiz(quiz, actor)
        return await self.quizzes.list_results_for_quiz(quiz_id)

    async def update_result(self, result_id: UUID, payload: QuizResultUpdate, actor: User) -> QuizResult:
        result = await self.quizzes.get_result_by_id(result_id)
        if result is None:
            raise AppException("Quiz result not found", HTTPStatus.NOT_FOUND)
        self._ensure_can_edit_quiz(result.quiz, actor)
        self._validate_earned_grade(payload.earned_grade, float(result.max_grade))
        if float(result.earned_grade) == payload.earned_grade:
            return result
        old_grade = float(result.earned_grade)
        if result.grade_entry_id is None:
            original_grade_entry = await self._create_quiz_grade_entry(result, result.quiz.source_type, actor)
            result.grade_entry_id = original_grade_entry.id
        correction = GradeEntry(
            student_id=result.student_id,
            class_id=result.quiz.class_id,
            teacher_id=result.quiz.teacher_id,
            category=GradeCategory.correction,
            earned_grade=payload.earned_grade - old_grade,
            max_grade=0,
            source_type=GradeSourceType.correction,
            reason=f"Quiz result correction from {old_grade:g} to {payload.earned_grade:g}",
            related_entry_id=result.grade_entry_id,
            created_by_user_id=actor.id,
        )
        await self.grades.add(correction)
        result.earned_grade = payload.earned_grade
        await self.audit_logs.add(
            actor.id,
            "update_quiz_result",
            "quiz_result",
            result.id,
            old_value={"earned_grade": old_grade},
            new_value={"earned_grade": payload.earned_grade, "correction_grade_entry_id": str(correction.id)},
        )
        await self.audit_logs.add(
            actor.id,
            "create_quiz_correction",
            "grade_entry",
            correction.id,
            new_value={"related_entry_id": str(result.grade_entry_id), "earned_grade": float(correction.earned_grade)},
        )
        await self.session.commit()
        return await self.quizzes.get_result_by_id(result.id)

    async def list_teacher_class_quizzes(self, class_id: UUID, actor: User) -> list[Quiz]:
        academic_class = await self._require_class(class_id)
        self._require_teacher_assigned(actor, academic_class)
        return await self.quizzes.list_quizzes_for_class(class_id)

    async def list_student_quiz_results(self, actor: User) -> list[QuizResult]:
        if actor.role != UserRole.student or actor.student_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self.quizzes.list_results_for_student(actor.student_profile.id)

    async def list_all_results_for_admin(self, actor: User) -> list[QuizResult]:
        if actor.role != UserRole.admin:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self.quizzes.list_results_all()

    async def _process_results(
        self,
        quiz: Quiz,
        rows: list[ManualQuizResultCreate],
        source_type: QuizSourceType,
        actor: User,
        errors: list[QuizUploadErrorRead],
    ) -> list[QuizResult]:
        active_enrollments = await self.enrollments.list_for_class(quiz.class_id)
        enrolled_students = {
            enrollment.student_id: enrollment.student
            for enrollment in active_enrollments
            if enrollment.status == EnrollmentStatus.active
            and enrollment.deleted_at is None
            and enrollment.student.status == StudentStatus.active
        }
        saved_results: list[QuizResult] = []
        for index, row in enumerate(rows, start=2):
            student = enrolled_students.get(row.student_id)
            if student is None:
                errors.append(
                    QuizUploadErrorRead(
                        row_number=row.row_number or index,
                        student_code=row.student_code,
                        reason="Student is not actively enrolled in this class",
                    )
                )
                continue
            try:
                self._validate_earned_grade(row.earned_grade, float(quiz.max_grade))
            except AppException as exc:
                errors.append(
                    QuizUploadErrorRead(row_number=row.row_number or index, student_code=row.student_code, reason=exc.message)
                )
                continue
            existing = await self.quizzes.get_result_for_quiz_student(quiz.id, row.student_id)
            if existing is None:
                result = QuizResult(
                    quiz_id=quiz.id,
                    student_id=row.student_id,
                    earned_grade=row.earned_grade,
                    max_grade=quiz.max_grade,
                )
                await self.quizzes.add_result(result)
                result.quiz = quiz
                grade_entry = await self._create_quiz_grade_entry(result, source_type, actor)
                result.grade_entry_id = grade_entry.id
                await self.audit_logs.add(
                    actor.id,
                    "create_quiz_result",
                    "quiz_result",
                    result.id,
                    new_value={"student_id": str(result.student_id), "earned_grade": float(result.earned_grade)},
                )
                saved_results.append(result)
                continue
            if float(existing.earned_grade) != row.earned_grade:
                saved_results.append(await self._update_existing_result_without_commit(existing, row.earned_grade, actor))
            else:
                if existing.grade_entry_id is None:
                    grade_entry = await self._create_quiz_grade_entry(existing, source_type, actor)
                    existing.grade_entry_id = grade_entry.id
                saved_results.append(existing)
        return saved_results

    async def _update_existing_result_without_commit(self, result: QuizResult, earned_grade: float, actor: User) -> QuizResult:
        old_grade = float(result.earned_grade)
        if result.grade_entry_id is None:
            original_grade_entry = await self._create_quiz_grade_entry(result, result.quiz.source_type, actor)
            result.grade_entry_id = original_grade_entry.id
        correction = GradeEntry(
            student_id=result.student_id,
            class_id=result.quiz.class_id,
            teacher_id=result.quiz.teacher_id,
            category=GradeCategory.correction,
            earned_grade=earned_grade - old_grade,
            max_grade=0,
            source_type=GradeSourceType.correction,
            reason=f"Quiz result correction from {old_grade:g} to {earned_grade:g}",
            related_entry_id=result.grade_entry_id,
            created_by_user_id=actor.id,
        )
        await self.grades.add(correction)
        result.earned_grade = earned_grade
        await self.audit_logs.add(
            actor.id,
            "update_quiz_result",
            "quiz_result",
            result.id,
            old_value={"earned_grade": old_grade},
            new_value={"earned_grade": earned_grade, "correction_grade_entry_id": str(correction.id)},
        )
        return result

    async def _create_quiz_grade_entry(self, result: QuizResult, source_type: QuizSourceType, actor: User) -> GradeEntry:
        grade_entry = GradeEntry(
            student_id=result.student_id,
            class_id=result.quiz.class_id,
            teacher_id=result.quiz.teacher_id,
            category=GradeCategory.quiz,
            earned_grade=result.earned_grade,
            max_grade=result.max_grade,
            source_type=GradeSourceType(source_type.value),
            reason="Quiz Result",
            created_by_user_id=actor.id,
        )
        await self.grades.add(grade_entry)
        await self.audit_logs.add(
            actor.id,
            "create_quiz_grade_entry",
            "grade_entry",
            grade_entry.id,
            new_value={
                "student_id": str(grade_entry.student_id),
                "class_id": str(grade_entry.class_id),
                "earned_grade": float(grade_entry.earned_grade),
            },
        )
        return grade_entry

    async def _get_or_create_quiz(
        self,
        class_id: UUID,
        teacher_id: UUID,
        title: str,
        description: str | None,
        quiz_date,
        max_grade: float,
        source_type: QuizSourceType,
        actor: User,
    ) -> Quiz:
        existing = await self.quizzes.get_quiz_by_identity(class_id, teacher_id, title, quiz_date)
        if existing is not None:
            if float(existing.max_grade) != float(max_grade):
                raise AppException("Quiz max_grade does not match existing quiz", HTTPStatus.BAD_REQUEST)
            return existing
        quiz = Quiz(
            class_id=class_id,
            teacher_id=teacher_id,
            title=title,
            description=description,
            quiz_date=quiz_date,
            max_grade=max_grade,
            source_type=source_type,
            created_by_user_id=actor.id,
        )
        await self.quizzes.add_quiz(quiz)
        await self.audit_logs.add(
            actor.id,
            "create_quiz",
            "quiz",
            quiz.id,
            new_value={"class_id": str(class_id), "teacher_id": str(teacher_id), "title": title},
        )
        return quiz

    async def _parse_csv(
        self,
        file: UploadFile,
        quiz_max_grade: float,
    ) -> tuple[list[ManualQuizResultCreate], list[QuizUploadErrorRead], int]:
        content = (await file.read()).decode("utf-8-sig")
        reader = csv.DictReader(StringIO(content))
        rows: list[ManualQuizResultCreate] = []
        errors: list[QuizUploadErrorRead] = []
        if reader.fieldnames is None or not {"student_code", "earned_grade", "max_grade"}.issubset(set(reader.fieldnames)):
            raise AppException("CSV must include student_code, earned_grade, and max_grade columns", HTTPStatus.BAD_REQUEST)
        students_by_code = await self._active_students_by_code()
        total_rows = 0
        for row_number, row in enumerate(reader, start=2):
            total_rows += 1
            student_code = (row.get("student_code") or "").strip()
            student = students_by_code.get(student_code)
            if student is None:
                errors.append(QuizUploadErrorRead(row_number=row_number, student_code=student_code, reason="Invalid student_code"))
                continue
            try:
                earned_grade = float((row.get("earned_grade") or "").strip())
            except ValueError:
                errors.append(QuizUploadErrorRead(row_number=row_number, student_code=student_code, reason="Invalid earned_grade"))
                continue
            try:
                row_max_grade = float((row.get("max_grade") or "").strip())
            except ValueError:
                errors.append(QuizUploadErrorRead(row_number=row_number, student_code=student_code, reason="Invalid max_grade"))
                continue
            if row_max_grade != quiz_max_grade:
                errors.append(QuizUploadErrorRead(row_number=row_number, student_code=student_code, reason="CSV max_grade does not match quiz max_grade"))
                continue
            if earned_grade > row_max_grade:
                errors.append(QuizUploadErrorRead(row_number=row_number, student_code=student_code, reason="earned_grade cannot exceed max_grade"))
                continue
            rows.append(
                ManualQuizResultCreate(
                    student_id=student.id,
                    earned_grade=earned_grade,
                    student_code=student_code,
                    row_number=row_number,
                )
            )
        return rows, errors, total_rows

    async def _active_students_by_code(self) -> dict[str, StudentProfile]:
        result = await self.session.scalars(select(StudentProfile).where(StudentProfile.status == StudentStatus.active))
        return {student.student_code: student for student in result.all()}

    async def _refresh_result(self, quiz_id: UUID, results: list[QuizResult]) -> dict:
        quiz = await self._require_quiz(quiz_id)
        result_ids = {result.id for result in results}
        refreshed_results = [result for result in await self.quizzes.list_results_for_quiz(quiz_id) if result.id in result_ids]
        return {"quiz": quiz, "results": refreshed_results}

    async def _require_class(self, class_id: UUID):
        academic_class = await self.academic.get_class(class_id)
        if academic_class is None:
            raise AppException("Class not found", HTTPStatus.NOT_FOUND)
        return academic_class

    async def _require_quiz(self, quiz_id: UUID) -> Quiz:
        quiz = await self.quizzes.get_quiz_by_id(quiz_id)
        if quiz is None:
            raise AppException("Quiz not found", HTTPStatus.NOT_FOUND)
        return quiz

    async def _resolve_teacher_id(self, actor: User, academic_class, teacher_id: UUID | None) -> UUID:
        if actor.role == UserRole.admin:
            if teacher_id is None:
                raise AppException("teacher_id is required for admin quiz", HTTPStatus.BAD_REQUEST)
            teacher = await self.academic.get_teacher_profile(teacher_id)
            if teacher is None:
                raise AppException("Teacher profile not found", HTTPStatus.NOT_FOUND)
            return teacher_id
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            if actor.teacher_profile.id not in {academic_class.instructor_id, academic_class.mentor_id}:
                raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
            return actor.teacher_profile.id
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    def _validate_earned_grade(self, earned_grade: float, max_grade: float) -> None:
        if earned_grade < 0:
            raise AppException("earned_grade must be greater than or equal to 0", HTTPStatus.BAD_REQUEST)
        if earned_grade > max_grade:
            raise AppException("earned_grade cannot exceed max_grade", HTTPStatus.BAD_REQUEST)

    def _ensure_can_view_quiz(self, quiz: Quiz, actor: User) -> None:
        if actor.role == UserRole.admin:
            return
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            if actor.teacher_profile.id in {quiz.academic_class.instructor_id, quiz.academic_class.mentor_id}:
                return
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    def _ensure_can_edit_quiz(self, quiz: Quiz, actor: User) -> None:
        if actor.role == UserRole.admin:
            return
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            if actor.teacher_profile.id in {quiz.academic_class.instructor_id, quiz.academic_class.mentor_id}:
                return
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    def _require_teacher_assigned(self, actor: User, academic_class) -> None:
        if actor.role != UserRole.teacher or actor.teacher_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        if actor.teacher_profile.id not in {academic_class.instructor_id, academic_class.mentor_id}:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
