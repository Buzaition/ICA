from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.domain.enums import FinalProjectStatus, UserRole
from app.models.final_project import FinalProject
from app.models.user import User
from app.repositories.academic import AcademicRepository
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.enrollments import EnrollmentRepository
from app.repositories.final_projects import FinalProjectRepository
from app.schemas.final_projects import FinalProjectReview, FinalProjectSubmit


class FinalProjectService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.academic = AcademicRepository(session)
        self.audit_logs = AuditLogRepository(session)
        self.enrollments = EnrollmentRepository(session)
        self.final_projects = FinalProjectRepository(session)

    async def submit_own_project(self, payload: FinalProjectSubmit, actor: User) -> FinalProject:
        enrollment = await self._require_student_active_enrollment(actor)
        existing = await self.final_projects.get_for_student_class_level(
            actor.student_profile.id,
            enrollment.class_id,
            enrollment.academic_class.level_id,
        )
        if existing is not None:
            if existing.status != FinalProjectStatus.pending:
                raise AppException("Final project cannot be edited after review", HTTPStatus.BAD_REQUEST)
            old_value = {"project_link": existing.project_link}
            existing.project_link = str(payload.project_link)
            await self.audit_logs.add(
                actor.id,
                "update_final_project",
                "final_project",
                existing.id,
                old_value=old_value,
                new_value={"project_link": existing.project_link},
            )
            await self.session.commit()
            return await self._require_final_project(existing.id)
        final_project = FinalProject(
            student_id=actor.student_profile.id,
            class_id=enrollment.class_id,
            level_id=enrollment.academic_class.level_id,
            project_link=str(payload.project_link),
            status=FinalProjectStatus.pending,
            submitted_at=datetime.now(UTC),
        )
        try:
            await self.final_projects.add(final_project)
            await self.audit_logs.add(
                actor.id,
                "submit_final_project",
                "final_project",
                final_project.id,
                new_value={
                    "student_id": str(final_project.student_id),
                    "class_id": str(final_project.class_id),
                    "level_id": str(final_project.level_id),
                },
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppException("Final project already exists for this class and level", HTTPStatus.BAD_REQUEST) from exc
        return await self._require_final_project(final_project.id)

    async def get_own_project(self, actor: User) -> FinalProject:
        enrollment = await self._require_student_active_enrollment(actor)
        final_project = await self.final_projects.get_for_student_active_class(actor.student_profile.id, enrollment.class_id)
        if final_project is None:
            raise AppException("Final project not found", HTTPStatus.NOT_FOUND)
        return final_project

    async def update_own_project(self, payload: FinalProjectSubmit, actor: User) -> FinalProject:
        final_project = await self.get_own_project(actor)
        if final_project.status != FinalProjectStatus.pending:
            raise AppException("Final project cannot be edited after review", HTTPStatus.BAD_REQUEST)
        old_value = {"project_link": final_project.project_link}
        final_project.project_link = str(payload.project_link)
        await self.audit_logs.add(
            actor.id,
            "update_final_project",
            "final_project",
            final_project.id,
            old_value=old_value,
            new_value={"project_link": final_project.project_link},
        )
        await self.session.commit()
        return await self._require_final_project(final_project.id)

    async def list_for_teacher_class(self, class_id: UUID, actor: User) -> list[FinalProject]:
        academic_class = await self.academic.get_class(class_id)
        if academic_class is None:
            raise AppException("Class not found", HTTPStatus.NOT_FOUND)
        if actor.role != UserRole.teacher or actor.teacher_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        if actor.teacher_profile.id not in {academic_class.instructor_id, academic_class.mentor_id}:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self.final_projects.list_for_class(class_id)

    async def list_all_for_admin(self, actor: User) -> list[FinalProject]:
        if actor.role != UserRole.admin:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self.final_projects.list_all()

    async def get_for_admin(self, final_project_id: UUID, actor: User) -> FinalProject:
        if actor.role != UserRole.admin:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self._require_final_project(final_project_id)

    async def review_project(self, final_project_id: UUID, payload: FinalProjectReview, actor: User) -> FinalProject:
        if actor.role != UserRole.admin or actor.admin_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        if payload.status not in {FinalProjectStatus.approved, FinalProjectStatus.rejected}:
            raise AppException("Review status must be approved or rejected", HTTPStatus.BAD_REQUEST)
        final_project = await self._require_final_project(final_project_id)
        old_value = {
            "status": final_project.status.value,
            "grade": float(final_project.grade) if final_project.grade is not None else None,
            "feedback": final_project.feedback,
        }
        final_project.status = payload.status
        final_project.grade = payload.grade
        final_project.feedback = payload.feedback
        final_project.reviewed_at = datetime.now(UTC)
        final_project.reviewed_by_admin_id = actor.admin_profile.id
        await self.audit_logs.add(
            actor.id,
            "review_final_project",
            "final_project",
            final_project.id,
            old_value=old_value,
            new_value={
                "status": final_project.status.value,
                "grade": final_project.grade,
                "feedback": final_project.feedback,
                "reviewed_by_admin_id": str(final_project.reviewed_by_admin_id),
            },
        )
        await self.session.commit()
        return await self._require_final_project(final_project.id)

    async def _require_final_project(self, final_project_id: UUID) -> FinalProject:
        final_project = await self.final_projects.get_by_id(final_project_id)
        if final_project is None:
            raise AppException("Final project not found", HTTPStatus.NOT_FOUND)
        return final_project

    async def _require_student_active_enrollment(self, actor: User):
        if actor.role != UserRole.student or actor.student_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        enrollment = await self.enrollments.get_active_for_student(actor.student_profile.id)
        if enrollment is None:
            raise AppException("Active class not found", HTTPStatus.NOT_FOUND)
        return enrollment
