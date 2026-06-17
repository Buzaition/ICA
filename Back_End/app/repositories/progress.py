from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.enums import EnrollmentStatus
from app.models.academic import Class as AcademicClass
from app.models.enrollment import ClassEnrollment
from app.models.grade import GradeEntry
from app.models.profiles import StudentProfile
from app.models.progress import ProgressSnapshot


class ProgressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_grade_entries_for_student_class(self, student_id: UUID, class_id: UUID) -> list[GradeEntry]:
        result = await self.session.scalars(
            select(GradeEntry)
            .options(
                selectinload(GradeEntry.related_entry),
                selectinload(GradeEntry.student),
                selectinload(GradeEntry.academic_class),
            )
            .where(
                GradeEntry.student_id == student_id,
                GradeEntry.class_id == class_id,
                GradeEntry.deleted_at.is_(None),
            )
            .order_by(GradeEntry.created_at)
        )
        return list(result.all())

    async def list_active_enrollments_for_class(self, class_id: UUID) -> list[ClassEnrollment]:
        result = await self.session.scalars(
            select(ClassEnrollment)
            .options(
                selectinload(ClassEnrollment.student).selectinload(StudentProfile.user),
                selectinload(ClassEnrollment.academic_class),
            )
            .where(
                ClassEnrollment.class_id == class_id,
                ClassEnrollment.status == EnrollmentStatus.active,
                ClassEnrollment.deleted_at.is_(None),
            )
            .order_by(ClassEnrollment.enrolled_at)
        )
        return list(result.all())

    async def add_snapshot(self, snapshot: ProgressSnapshot) -> ProgressSnapshot:
        self.session.add(snapshot)
        await self.session.flush()
        await self.session.refresh(snapshot)
        return snapshot

    async def list_snapshots_for_class(self, class_id: UUID) -> list[ProgressSnapshot]:
        result = await self.session.scalars(
            select(ProgressSnapshot)
            .options(
                selectinload(ProgressSnapshot.student),
                selectinload(ProgressSnapshot.academic_class),
            )
            .where(ProgressSnapshot.class_id == class_id)
            .order_by(ProgressSnapshot.created_at.desc())
        )
        return list(result.all())
