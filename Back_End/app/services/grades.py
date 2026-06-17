from http import HTTPStatus
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.domain.enums import AssignmentSubmissionStatus, GradeCategory, GradeSourceType, UserRole
from app.models.assignment import AssignmentSubmission
from app.models.grade import GradeEntry
from app.models.user import User
from app.repositories.academic import AcademicRepository
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.grades import GradeRepository
from app.schemas.grades import CorrectionCreate


class GradeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.academic = AcademicRepository(session)
        self.grades = GradeRepository(session)
        self.audit_logs = AuditLogRepository(session)

    async def create_assignment_grade_entry(
        self,
        submission: AssignmentSubmission,
        actor: User,
        commit: bool = True,
    ) -> GradeEntry:
        existing = await self.grades.get_by_assignment_submission_id(submission.id)
        if existing is not None:
            return existing
        if submission.status != AssignmentSubmissionStatus.reviewed or submission.grade is None:
            raise AppException("Submission must be reviewed before creating a grade entry", HTTPStatus.BAD_REQUEST)
        grade_entry = GradeEntry(
            student_id=submission.student_id,
            class_id=submission.assignment.class_id,
            teacher_id=submission.reviewed_by_teacher_id,
            category=GradeCategory.assignment,
            earned_grade=submission.grade,
            max_grade=submission.assignment.max_grade,
            source_type=GradeSourceType.manual,
            reason="Assignment Review",
            assignment_submission_id=submission.id,
            created_by_user_id=actor.id,
        )
        await self.grades.add(grade_entry)
        await self.audit_logs.add(
            actor.id,
            "create_grade_entry",
            "grade_entry",
            grade_entry.id,
            new_value={
                "student_id": str(grade_entry.student_id),
                "class_id": str(grade_entry.class_id),
                "category": grade_entry.category.value,
                "earned_grade": float(grade_entry.earned_grade),
                "max_grade": float(grade_entry.max_grade),
            },
        )
        if commit:
            await self.session.commit()
            refreshed = await self.grades.get_by_id(grade_entry.id)
            return refreshed
        return grade_entry

    async def list_grade_entries_for_user(self, actor: User) -> list[GradeEntry]:
        if actor.role == UserRole.admin:
            return await self.grades.list_all()
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            return await self.grades.list_for_teacher(actor.teacher_profile.id)
        if actor.role == UserRole.student and actor.student_profile is not None:
            return await self.grades.list_for_student(actor.student_profile.id)
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    async def get_grade_entry_for_user(self, grade_entry_id: UUID, actor: User) -> GradeEntry:
        grade_entry = await self.grades.get_by_id(grade_entry_id)
        if grade_entry is None:
            raise AppException("Grade entry not found", HTTPStatus.NOT_FOUND)
        self._ensure_can_view_grade_entry(grade_entry, actor)
        return grade_entry

    async def list_student_grade_entries(self, actor: User) -> list[GradeEntry]:
        if actor.role != UserRole.student or actor.student_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self.grades.list_for_student(actor.student_profile.id)

    async def list_teacher_class_grade_entries(self, class_id: UUID, actor: User) -> list[GradeEntry]:
        academic_class = await self.academic.get_class(class_id)
        if academic_class is None:
            raise AppException("Class not found", HTTPStatus.NOT_FOUND)
        self._require_teacher_assigned(actor, academic_class)
        return await self.grades.list_for_class(class_id)

    async def create_correction(self, grade_entry_id: UUID, payload: CorrectionCreate, actor: User) -> GradeEntry:
        original = await self.grades.get_by_id(grade_entry_id)
        if original is None:
            raise AppException("Grade entry not found", HTTPStatus.NOT_FOUND)
        if original.category == GradeCategory.correction:
            raise AppException("Cannot create correction for correction entry", HTTPStatus.BAD_REQUEST)
        if actor.role == UserRole.admin:
            teacher_id = original.teacher_id
        elif actor.role == UserRole.teacher and actor.teacher_profile is not None:
            if actor.teacher_profile.id not in {original.academic_class.instructor_id, original.academic_class.mentor_id}:
                raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
            teacher_id = actor.teacher_profile.id
        else:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        correction = GradeEntry(
            student_id=original.student_id,
            class_id=original.class_id,
            teacher_id=teacher_id,
            category=GradeCategory.correction,
            earned_grade=payload.earned_grade,
            max_grade=0,
            source_type=GradeSourceType.correction,
            reason=payload.reason,
            related_entry_id=original.id,
            created_by_user_id=actor.id,
        )
        await self.grades.add(correction)
        await self.audit_logs.add(
            actor.id,
            "create_grade_correction",
            "grade_entry",
            correction.id,
            new_value={
                "related_entry_id": str(original.id),
                "earned_grade": float(correction.earned_grade),
                "reason": correction.reason,
            },
        )
        await self.session.commit()
        return await self.grades.get_by_id(correction.id)

    async def list_corrections_for_entry(self, grade_entry_id: UUID, actor: User) -> list[GradeEntry]:
        original = await self.get_grade_entry_for_user(grade_entry_id, actor)
        return await self.grades.list_corrections_for_entry(original.id)

    async def list_teacher_corrections_history(self, actor: User) -> list[GradeEntry]:
        if actor.role != UserRole.teacher or actor.teacher_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self.grades.list_corrections_for_teacher(actor.teacher_profile.id)

    async def list_admin_corrections_history(self, actor: User) -> list[GradeEntry]:
        if actor.role != UserRole.admin:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self.grades.list_corrections_all()

    def _ensure_can_view_grade_entry(self, grade_entry: GradeEntry, actor: User) -> None:
        if actor.role == UserRole.admin:
            return
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            if actor.teacher_profile.id in {grade_entry.academic_class.instructor_id, grade_entry.academic_class.mentor_id}:
                return
        if actor.role == UserRole.student and actor.student_profile is not None:
            if actor.student_profile.id == grade_entry.student_id:
                return
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    def _require_teacher_assigned(self, actor: User, academic_class) -> None:
        if actor.role != UserRole.teacher or actor.teacher_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        if actor.teacher_profile.id not in {academic_class.instructor_id, academic_class.mentor_id}:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
