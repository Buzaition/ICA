from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.enums import AssignmentSubmissionStatus
from app.models.academic import Class as AcademicClass
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.profiles import StudentProfile


class AssignmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, entity):
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def get_assignment(self, assignment_id: UUID, include_deleted: bool = False) -> Assignment | None:
        statement = self._assignment_query().where(Assignment.id == assignment_id)
        if not include_deleted:
            statement = statement.where(Assignment.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def list_assignments(self) -> list[Assignment]:
        result = await self.session.scalars(
            self._assignment_query().where(Assignment.deleted_at.is_(None)).order_by(Assignment.created_at.desc())
        )
        return list(result.all())

    async def list_assignments_for_class(self, class_id: UUID) -> list[Assignment]:
        result = await self.session.scalars(
            self._assignment_query()
            .where(Assignment.class_id == class_id, Assignment.deleted_at.is_(None), Assignment.is_active.is_(True))
            .order_by(Assignment.deadline)
        )
        return list(result.all())

    async def list_assignments_for_teacher(self, teacher_profile_id: UUID) -> list[Assignment]:
        result = await self.session.scalars(
            self._assignment_query()
            .where(
                Assignment.deleted_at.is_(None),
                or_(
                    AcademicClass.instructor_id == teacher_profile_id,
                    AcademicClass.mentor_id == teacher_profile_id,
                ),
            )
            .join(Assignment.academic_class)
            .order_by(Assignment.deadline)
        )
        return list(result.all())

    async def add_submission(self, submission: AssignmentSubmission) -> AssignmentSubmission:
        self.session.add(submission)
        await self.session.flush()
        await self.session.refresh(submission)
        return submission

    async def get_submission(self, submission_id: UUID, include_deleted: bool = False) -> AssignmentSubmission | None:
        statement = self._submission_query().where(AssignmentSubmission.id == submission_id)
        if not include_deleted:
            statement = statement.where(AssignmentSubmission.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def list_submissions(self) -> list[AssignmentSubmission]:
        result = await self.session.scalars(self._submission_query().order_by(AssignmentSubmission.submitted_at.desc()))
        return list(result.all())

    async def list_submissions_for_student(self, student_id: UUID) -> list[AssignmentSubmission]:
        result = await self.session.scalars(
            self._submission_query()
            .where(AssignmentSubmission.student_id == student_id, AssignmentSubmission.deleted_at.is_(None))
            .order_by(AssignmentSubmission.submitted_at.desc())
        )
        return list(result.all())

    async def get_latest_active_submission(self, assignment_id: UUID, student_id: UUID) -> AssignmentSubmission | None:
        return await self.session.scalar(
            self._submission_query()
            .where(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.student_id == student_id,
                AssignmentSubmission.deleted_at.is_(None),
                AssignmentSubmission.status.in_(
                    [AssignmentSubmissionStatus.submitted, AssignmentSubmissionStatus.late, AssignmentSubmissionStatus.reviewed]
                ),
            )
            .order_by(AssignmentSubmission.submitted_at.desc())
        )

    async def list_pending_for_teacher(self, teacher_profile_id: UUID) -> list[AssignmentSubmission]:
        return await self._list_submissions_for_teacher(
            teacher_profile_id,
            AssignmentSubmission.reviewed_at.is_(None),
            AssignmentSubmission.grade.is_(None),
            AssignmentSubmission.status.in_([AssignmentSubmissionStatus.submitted, AssignmentSubmissionStatus.late]),
        )

    async def list_reviewed_for_teacher(self, teacher_profile_id: UUID) -> list[AssignmentSubmission]:
        return await self._list_submissions_for_teacher(
            teacher_profile_id,
            AssignmentSubmission.status == AssignmentSubmissionStatus.reviewed,
            AssignmentSubmission.reviewed_at.is_not(None),
        )

    async def list_late_for_teacher(self, teacher_profile_id: UUID) -> list[AssignmentSubmission]:
        return await self._list_submissions_for_teacher(
            teacher_profile_id,
            AssignmentSubmission.status == AssignmentSubmissionStatus.late,
            AssignmentSubmission.reviewed_at.is_(None),
        )

    async def _list_submissions_for_teacher(self, teacher_profile_id: UUID, *criteria) -> list[AssignmentSubmission]:
        result = await self.session.scalars(
            self._submission_query()
            .join(AssignmentSubmission.assignment)
            .join(Assignment.academic_class)
            .where(
                AssignmentSubmission.deleted_at.is_(None),
                Assignment.deleted_at.is_(None),
                or_(
                    AcademicClass.instructor_id == teacher_profile_id,
                    AcademicClass.mentor_id == teacher_profile_id,
                ),
                and_(*criteria),
            )
            .order_by(AssignmentSubmission.submitted_at.desc())
        )
        return list(result.all())

    def _assignment_query(self):
        return select(Assignment).options(
            selectinload(Assignment.created_by_teacher),
            selectinload(Assignment.academic_class).selectinload(AcademicClass.branch),
            selectinload(Assignment.academic_class).selectinload(AcademicClass.cycle),
            selectinload(Assignment.academic_class).selectinload(AcademicClass.track),
            selectinload(Assignment.academic_class).selectinload(AcademicClass.level),
        )

    def _submission_query(self):
        return select(AssignmentSubmission).options(
            selectinload(AssignmentSubmission.student).selectinload(StudentProfile.user),
            selectinload(AssignmentSubmission.reviewed_by_teacher),
            selectinload(AssignmentSubmission.grade_entries),
            selectinload(AssignmentSubmission.assignment).selectinload(Assignment.created_by_teacher),
            selectinload(AssignmentSubmission.assignment).selectinload(Assignment.academic_class).selectinload(AcademicClass.branch),
            selectinload(AssignmentSubmission.assignment).selectinload(Assignment.academic_class).selectinload(AcademicClass.cycle),
            selectinload(AssignmentSubmission.assignment).selectinload(Assignment.academic_class).selectinload(AcademicClass.track),
            selectinload(AssignmentSubmission.assignment).selectinload(Assignment.academic_class).selectinload(AcademicClass.level),
        )
