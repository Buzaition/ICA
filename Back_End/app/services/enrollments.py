from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.domain.enums import ClassStatus, EnrollmentStatus, StudentStatus, UserRole
from app.models.enrollment import ClassEnrollment
from app.models.user import User
from app.repositories.academic import AcademicRepository
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.enrollments import EnrollmentRepository
from app.schemas.enrollments import EnrollmentCreate


class EnrollmentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.academic = AcademicRepository(session)
        self.enrollments = EnrollmentRepository(session)
        self.audit_logs = AuditLogRepository(session)

    async def create_enrollment(self, payload: EnrollmentCreate, actor: User) -> ClassEnrollment:
        student = await self.enrollments.get_student_profile(payload.student_id)
        academic_class = await self.academic.get_class(payload.class_id)
        if student is None:
            raise AppException("Student not found", HTTPStatus.NOT_FOUND)
        if academic_class is None:
            raise AppException("Class not found", HTTPStatus.NOT_FOUND)
        if student.status != StudentStatus.active:
            raise AppException("Only active students can be enrolled", HTTPStatus.BAD_REQUEST)
        if academic_class.status in {ClassStatus.cancelled, ClassStatus.completed}:
            raise AppException("Cannot enroll into a cancelled or completed class", HTTPStatus.BAD_REQUEST)
        if await self.enrollments.get_active_for_student(student.id) is not None:
            raise AppException("Student already has an active enrollment", HTTPStatus.BAD_REQUEST)
        active_count = await self.enrollments.count_active_for_class(academic_class.id)
        if active_count >= academic_class.max_students:
            raise AppException("Class capacity has been reached", HTTPStatus.BAD_REQUEST)
        enrollment = ClassEnrollment(
            student_id=student.id,
            class_id=academic_class.id,
            status=EnrollmentStatus.active,
        )
        try:
            await self.enrollments.add(enrollment)
            await self.audit_logs.add(
                actor.id,
                "create_enrollment",
                "class_enrollment",
                enrollment.id,
                new_value={"student_id": str(student.id), "class_id": str(academic_class.id)},
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppException("Student already has an active enrollment", HTTPStatus.BAD_REQUEST) from exc
        return await self.get_enrollment(enrollment.id)

    async def list_enrollments(self) -> list[ClassEnrollment]:
        return await self.enrollments.list_all(include_deleted=True)

    async def get_enrollment(self, enrollment_id: UUID) -> ClassEnrollment:
        enrollment = await self.enrollments.get_by_id(enrollment_id, include_deleted=True)
        if enrollment is None:
            raise AppException("Enrollment not found", HTTPStatus.NOT_FOUND)
        return enrollment

    async def remove_enrollment(self, enrollment_id: UUID, actor: User) -> None:
        enrollment = await self.get_enrollment(enrollment_id)
        if enrollment.status != EnrollmentStatus.removed:
            now = datetime.now(UTC)
            enrollment.status = EnrollmentStatus.removed
            enrollment.removed_at = now
            enrollment.deleted_at = now
        await self.audit_logs.add(
            actor.id,
            "remove_enrollment",
            "class_enrollment",
            enrollment.id,
            old_value={"status": EnrollmentStatus.active.value},
            new_value={"status": EnrollmentStatus.removed.value},
        )
        await self.session.commit()

    async def list_students_for_teacher_class(self, class_id: UUID, actor: User) -> list[ClassEnrollment]:
        academic_class = await self.academic.get_class(class_id)
        if academic_class is None:
            raise AppException("Class not found", HTTPStatus.NOT_FOUND)
        if actor.role != UserRole.teacher or actor.teacher_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        if actor.teacher_profile.id not in {academic_class.instructor_id, academic_class.mentor_id}:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self.enrollments.list_for_class(class_id)

    async def get_student_active_class(self, actor: User) -> ClassEnrollment:
        if actor.role != UserRole.student or actor.student_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        enrollment = await self.enrollments.get_active_for_student(actor.student_profile.id)
        if enrollment is None:
            raise AppException("Active class not found", HTTPStatus.NOT_FOUND)
        return enrollment
