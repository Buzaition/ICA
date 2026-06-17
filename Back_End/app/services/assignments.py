from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.domain.enums import AssignmentSubmissionStatus, UserRole
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.user import User
from app.repositories.academic import AcademicRepository
from app.repositories.assignments import AssignmentRepository
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.enrollments import EnrollmentRepository
from app.schemas.assignments import AssignmentCreate, AssignmentUpdate, SubmissionCreate, SubmissionReject, SubmissionReview


class AssignmentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.academic = AcademicRepository(session)
        self.assignments = AssignmentRepository(session)
        self.audit_logs = AuditLogRepository(session)
        self.enrollments = EnrollmentRepository(session)

    async def create_assignment(self, payload: AssignmentCreate, actor: User) -> Assignment:
        academic_class = await self.academic.get_class(payload.class_id)
        if academic_class is None:
            raise AppException("Class not found", HTTPStatus.NOT_FOUND)
        if actor.role == UserRole.admin:
            if payload.created_by_teacher_id is None:
                raise AppException("created_by_teacher_id is required for admin-created assignments", HTTPStatus.BAD_REQUEST)
            teacher = await self.academic.get_teacher_profile(payload.created_by_teacher_id)
            if teacher is None:
                raise AppException("Teacher profile not found", HTTPStatus.NOT_FOUND)
            created_by_teacher_id = payload.created_by_teacher_id
        elif actor.role == UserRole.teacher and actor.teacher_profile is not None:
            if actor.teacher_profile.id not in {academic_class.instructor_id, academic_class.mentor_id}:
                raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
            created_by_teacher_id = actor.teacher_profile.id
        else:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        assignment = Assignment(
            class_id=payload.class_id,
            created_by_teacher_id=created_by_teacher_id,
            title=payload.title,
            description=payload.description,
            requirement_url=str(payload.requirement_url),
            deadline=payload.deadline,
            max_grade=payload.max_grade,
            is_active=True,
        )
        await self.assignments.add(assignment)
        await self.audit_logs.add(
            actor.id,
            "create_assignment",
            "assignment",
            assignment.id,
            new_value={"class_id": str(assignment.class_id), "title": assignment.title},
        )
        await self.session.commit()
        return await self.get_assignment_for_user(assignment.id, actor)

    async def list_assignments_for_user(self, actor: User) -> list[Assignment]:
        if actor.role == UserRole.admin:
            return await self.assignments.list_assignments()
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            return await self.assignments.list_assignments_for_teacher(actor.teacher_profile.id)
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    async def list_student_assignments(self, actor: User) -> list[Assignment]:
        enrollment = await self._require_student_active_enrollment(actor)
        return await self.assignments.list_assignments_for_class(enrollment.class_id)

    async def list_teacher_class_assignments(self, class_id: UUID, actor: User) -> list[Assignment]:
        academic_class = await self.academic.get_class(class_id)
        if academic_class is None:
            raise AppException("Class not found", HTTPStatus.NOT_FOUND)
        self._require_teacher_assigned(actor, academic_class)
        return await self.assignments.list_assignments_for_class(class_id)

    async def get_assignment_for_user(self, assignment_id: UUID, actor: User) -> Assignment:
        assignment = await self._require_assignment(assignment_id)
        if actor.role == UserRole.admin:
            return assignment
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            if actor.teacher_profile.id in {assignment.academic_class.instructor_id, assignment.academic_class.mentor_id}:
                return assignment
        if actor.role == UserRole.student and actor.student_profile is not None:
            enrollment = await self.enrollments.get_active_for_student(actor.student_profile.id)
            if enrollment is not None and enrollment.class_id == assignment.class_id:
                return assignment
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    async def update_assignment(self, assignment_id: UUID, payload: AssignmentUpdate, actor: User) -> Assignment:
        assignment = await self._require_assignment(assignment_id)
        if actor.role != UserRole.admin:
            self._require_teacher_assigned(actor, assignment.academic_class)
        old_value = {"title": assignment.title, "max_grade": float(assignment.max_grade), "is_active": assignment.is_active}
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(assignment, field, str(value) if field == "requirement_url" and value is not None else value)
        await self.audit_logs.add(
            actor.id,
            "update_assignment",
            "assignment",
            assignment.id,
            old_value=old_value,
            new_value={"title": assignment.title, "max_grade": float(assignment.max_grade), "is_active": assignment.is_active},
        )
        await self.session.commit()
        return await self.get_assignment_for_user(assignment.id, actor)

    async def delete_assignment(self, assignment_id: UUID, actor: User) -> None:
        assignment = await self._require_assignment(assignment_id)
        if actor.role != UserRole.admin:
            self._require_teacher_assigned(actor, assignment.academic_class)
        assignment.deleted_at = datetime.now(UTC)
        await self.audit_logs.add(actor.id, "delete_assignment", "assignment", assignment.id)
        await self.session.commit()

    async def submit_assignment(self, assignment_id: UUID, payload: SubmissionCreate, actor: User) -> AssignmentSubmission:
        assignment = await self._require_assignment(assignment_id)
        enrollment = await self._require_student_active_enrollment(actor)
        if enrollment.class_id != assignment.class_id:
            raise AppException("Assignment is not in student's active class", HTTPStatus.FORBIDDEN)
        now = datetime.now(UTC)
        deadline = assignment.deadline if assignment.deadline.tzinfo else assignment.deadline.replace(tzinfo=UTC)
        latest = await self.assignments.get_latest_active_submission(assignment.id, actor.student_profile.id)
        if latest is not None and latest.status == AssignmentSubmissionStatus.reviewed and now > deadline:
            raise AppException("Cannot resubmit after deadline when submission is already reviewed", HTTPStatus.BAD_REQUEST)
        if latest is not None and now <= deadline:
            latest.status = AssignmentSubmissionStatus.replaced
        status = AssignmentSubmissionStatus.submitted if now <= deadline else AssignmentSubmissionStatus.late
        submission = AssignmentSubmission(
            assignment_id=assignment.id,
            student_id=actor.student_profile.id,
            submission_url=str(payload.submission_url),
            submitted_at=now,
            status=status,
        )
        await self.assignments.add_submission(submission)
        await self.audit_logs.add(
            actor.id,
            "submit_assignment",
            "assignment_submission",
            submission.id,
            new_value={"assignment_id": str(assignment.id), "status": status.value},
        )
        await self.session.commit()
        return await self._require_submission(submission.id)

    async def list_student_submissions(self, actor: User) -> list[AssignmentSubmission]:
        if actor.role != UserRole.student or actor.student_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self.assignments.list_submissions_for_student(actor.student_profile.id)

    async def list_admin_submissions(self) -> list[AssignmentSubmission]:
        return await self.assignments.list_submissions()

    async def get_submission_for_admin(self, submission_id: UUID) -> AssignmentSubmission:
        return await self._require_submission(submission_id)

    async def list_pending_for_teacher(self, actor: User) -> list[AssignmentSubmission]:
        self._require_teacher(actor)
        return await self.assignments.list_pending_for_teacher(actor.teacher_profile.id)

    async def list_reviewed_for_teacher(self, actor: User) -> list[AssignmentSubmission]:
        self._require_teacher(actor)
        return await self.assignments.list_reviewed_for_teacher(actor.teacher_profile.id)

    async def list_late_for_teacher(self, actor: User) -> list[AssignmentSubmission]:
        self._require_teacher(actor)
        return await self.assignments.list_late_for_teacher(actor.teacher_profile.id)

    async def review_submission(self, submission_id: UUID, payload: SubmissionReview, actor: User) -> AssignmentSubmission:
        submission = await self._require_submission(submission_id)
        reviewer_id = await self._resolve_reviewer_id(actor, submission, getattr(payload, "reviewed_by_teacher_id", None))
        if submission.status == AssignmentSubmissionStatus.reviewed:
            from app.services.grades import GradeService

            grade_entry = await GradeService(self.session).create_assignment_grade_entry(submission, actor, commit=False)
            await self.session.commit()
            refreshed = await self._require_submission(submission.id)
            setattr(refreshed, "grade_entry_id", grade_entry.id)
            return refreshed
        if payload.grade > float(submission.assignment.max_grade):
            raise AppException("Grade cannot exceed assignment max_grade", HTTPStatus.BAD_REQUEST)
        submission.grade = payload.grade
        submission.feedback = payload.feedback
        submission.reviewed_at = datetime.now(UTC)
        submission.reviewed_by_teacher_id = reviewer_id
        submission.status = AssignmentSubmissionStatus.reviewed
        from app.services.grades import GradeService

        grade_entry = await GradeService(self.session).create_assignment_grade_entry(submission, actor, commit=False)
        await self.audit_logs.add(
            actor.id,
            "review_assignment_submission",
            "assignment_submission",
            submission.id,
            new_value={"grade": payload.grade, "reviewed_by_teacher_id": str(reviewer_id)},
        )
        await self.session.commit()
        refreshed = await self._require_submission(submission.id)
        setattr(refreshed, "grade_entry_id", grade_entry.id)
        return refreshed

    async def reject_submission(self, submission_id: UUID, payload: SubmissionReject, actor: User) -> AssignmentSubmission:
        submission = await self._require_submission(submission_id)
        reviewer_id = await self._resolve_reviewer_id(actor, submission, payload.reviewed_by_teacher_id)
        submission.grade = None
        submission.feedback = payload.feedback
        submission.reviewed_at = datetime.now(UTC)
        submission.reviewed_by_teacher_id = reviewer_id
        submission.status = AssignmentSubmissionStatus.rejected
        await self.audit_logs.add(
            actor.id,
            "reject_assignment_submission",
            "assignment_submission",
            submission.id,
            new_value={"reviewed_by_teacher_id": str(reviewer_id)},
        )
        await self.session.commit()
        return await self._require_submission(submission.id)

    async def _require_assignment(self, assignment_id: UUID) -> Assignment:
        assignment = await self.assignments.get_assignment(assignment_id)
        if assignment is None:
            raise AppException("Assignment not found", HTTPStatus.NOT_FOUND)
        return assignment

    async def _require_submission(self, submission_id: UUID) -> AssignmentSubmission:
        submission = await self.assignments.get_submission(submission_id)
        if submission is None:
            raise AppException("Submission not found", HTTPStatus.NOT_FOUND)
        return submission

    async def _require_student_active_enrollment(self, actor: User):
        if actor.role != UserRole.student or actor.student_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        enrollment = await self.enrollments.get_active_for_student(actor.student_profile.id)
        if enrollment is None:
            raise AppException("Active class not found", HTTPStatus.NOT_FOUND)
        return enrollment

    def _require_teacher(self, actor: User) -> None:
        if actor.role != UserRole.teacher or actor.teacher_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    def _require_teacher_assigned(self, actor: User, academic_class) -> None:
        self._require_teacher(actor)
        if actor.teacher_profile.id not in {academic_class.instructor_id, academic_class.mentor_id}:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    async def _resolve_reviewer_id(self, actor: User, submission: AssignmentSubmission, reviewer_id: UUID | None) -> UUID:
        if actor.role == UserRole.admin:
            if reviewer_id is None:
                raise AppException("reviewed_by_teacher_id is required for admin review", HTTPStatus.BAD_REQUEST)
            teacher = await self.academic.get_teacher_profile(reviewer_id)
            if teacher is None:
                raise AppException("Teacher profile not found", HTTPStatus.NOT_FOUND)
            return reviewer_id
        self._require_teacher_assigned(actor, submission.assignment.academic_class)
        return actor.teacher_profile.id
