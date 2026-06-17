from datetime import UTC, datetime, time, timedelta
from http import HTTPStatus
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.domain.enums import EnrollmentStatus, GradeCategory, GradeSourceType, StudentStatus, UserRole
from app.models.grade import GradeEntry
from app.models.user import User
from app.repositories.academic import AcademicRepository
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.enrollments import EnrollmentRepository
from app.repositories.grades import GradeRepository
from app.schemas.bonus import BonusCreate


WEEKLY_BONUS_LIMIT = 5


class BonusService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.academic = AcademicRepository(session)
        self.audit_logs = AuditLogRepository(session)
        self.enrollments = EnrollmentRepository(session)
        self.grades = GradeRepository(session)

    async def create_bonus(self, payload: BonusCreate, actor: User) -> tuple[GradeEntry, int, int]:
        academic_class = await self.academic.get_class(payload.class_id)
        if academic_class is None:
            raise AppException("Class not found", HTTPStatus.NOT_FOUND)
        student = await self.enrollments.get_student_profile(payload.student_id)
        if student is None:
            raise AppException("Student profile not found", HTTPStatus.NOT_FOUND)
        if student.status != StudentStatus.active:
            raise AppException("Student is not active", HTTPStatus.BAD_REQUEST)
        enrollment = await self.enrollments.get_active_for_student(payload.student_id)
        if enrollment is None or enrollment.class_id != payload.class_id or enrollment.status != EnrollmentStatus.active:
            raise AppException("Student is not actively enrolled in this class", HTTPStatus.BAD_REQUEST)
        teacher_id = None
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            if actor.teacher_profile.id not in {academic_class.instructor_id, academic_class.mentor_id}:
                raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
            teacher_id = actor.teacher_profile.id
        elif actor.role != UserRole.admin:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        start_at, end_at = self._current_iso_week_window()
        current_count = await self.grades.count_bonus_for_student_class_between(
            payload.student_id,
            payload.class_id,
            start_at,
            end_at,
        )
        if current_count >= WEEKLY_BONUS_LIMIT:
            raise AppException("Weekly bonus limit exceeded", HTTPStatus.BAD_REQUEST)
        grade_entry = GradeEntry(
            student_id=payload.student_id,
            class_id=payload.class_id,
            teacher_id=teacher_id,
            category=GradeCategory.bonus,
            earned_grade=1,
            max_grade=0,
            source_type=GradeSourceType.system_bonus,
            reason=payload.reason or "Bonus",
            created_by_user_id=actor.id,
        )
        await self.grades.add(grade_entry)
        await self.audit_logs.add(
            actor.id,
            "create_bonus",
            "grade_entry",
            grade_entry.id,
            new_value={
                "student_id": str(grade_entry.student_id),
                "class_id": str(grade_entry.class_id),
                "earned_grade": 1,
                "reason": grade_entry.reason,
            },
        )
        await self.session.commit()
        refreshed = await self.grades.get_by_id(grade_entry.id)
        weekly_count = current_count + 1
        return refreshed, weekly_count, WEEKLY_BONUS_LIMIT - weekly_count

    async def list_bonus_for_user(self, actor: User) -> list[GradeEntry]:
        if actor.role == UserRole.admin:
            return await self.grades.list_bonus_all()
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            return await self.grades.list_bonus_for_teacher(actor.teacher_profile.id)
        if actor.role == UserRole.student and actor.student_profile is not None:
            return await self.grades.list_bonus_for_student(actor.student_profile.id)
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    async def list_student_bonus(self, actor: User) -> list[GradeEntry]:
        if actor.role != UserRole.student or actor.student_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self.grades.list_bonus_for_student(actor.student_profile.id)

    async def list_teacher_class_bonus(self, class_id: UUID, actor: User) -> list[GradeEntry]:
        academic_class = await self.academic.get_class(class_id)
        if academic_class is None:
            raise AppException("Class not found", HTTPStatus.NOT_FOUND)
        if actor.role != UserRole.teacher or actor.teacher_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        if actor.teacher_profile.id not in {academic_class.instructor_id, academic_class.mentor_id}:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self.grades.list_bonus_for_class(class_id)

    async def weekly_counts_for_entries(self, entries: list[GradeEntry]) -> dict[UUID, tuple[int, int]]:
        counts: dict[UUID, tuple[int, int]] = {}
        for entry in entries:
            start_at, end_at = self._iso_week_window(entry.created_at)
            count = await self.grades.count_bonus_for_student_class_between(
                entry.student_id,
                entry.class_id,
                start_at,
                end_at,
            )
            counts[entry.id] = (count, max(WEEKLY_BONUS_LIMIT - count, 0))
        return counts

    def _current_iso_week_window(self) -> tuple[datetime, datetime]:
        return self._iso_week_window(datetime.now(UTC))

    def _iso_week_window(self, value: datetime) -> tuple[datetime, datetime]:
        aware_value = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        iso_year, iso_week, _ = aware_value.isocalendar()
        monday = datetime.fromisocalendar(iso_year, iso_week, 1).date()
        start_at = datetime.combine(monday, time.min, tzinfo=UTC)
        return start_at, start_at + timedelta(days=7)
