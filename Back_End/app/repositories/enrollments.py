from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.enums import EnrollmentStatus
from app.models.academic import Class as AcademicClass
from app.models.enrollment import ClassEnrollment
from app.models.profiles import StudentProfile


class EnrollmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, enrollment: ClassEnrollment) -> ClassEnrollment:
        self.session.add(enrollment)
        await self.session.flush()
        await self.session.refresh(enrollment)
        return enrollment

    async def get_by_id(self, enrollment_id: UUID, include_deleted: bool = False) -> ClassEnrollment | None:
        statement = self._enrollment_query().where(ClassEnrollment.id == enrollment_id)
        if not include_deleted:
            statement = statement.where(ClassEnrollment.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def list_all(self, include_deleted: bool = False) -> list[ClassEnrollment]:
        statement = self._enrollment_query().order_by(ClassEnrollment.created_at.desc())
        if not include_deleted:
            statement = statement.where(ClassEnrollment.deleted_at.is_(None))
        result = await self.session.scalars(statement)
        return list(result.all())

    async def list_for_class(self, class_id: UUID) -> list[ClassEnrollment]:
        result = await self.session.scalars(
            self._enrollment_query()
            .where(
                ClassEnrollment.class_id == class_id,
                ClassEnrollment.status == EnrollmentStatus.active,
                ClassEnrollment.deleted_at.is_(None),
            )
            .order_by(ClassEnrollment.enrolled_at)
        )
        return list(result.all())

    async def get_active_for_student(self, student_id: UUID) -> ClassEnrollment | None:
        return await self.session.scalar(
            self._enrollment_query().where(
                ClassEnrollment.student_id == student_id,
                ClassEnrollment.status == EnrollmentStatus.active,
                ClassEnrollment.deleted_at.is_(None),
            )
        )

    async def count_active_for_class(self, class_id: UUID) -> int:
        count = await self.session.scalar(
            select(func.count(ClassEnrollment.id)).where(
                ClassEnrollment.class_id == class_id,
                ClassEnrollment.status == EnrollmentStatus.active,
                ClassEnrollment.deleted_at.is_(None),
            )
        )
        return int(count or 0)

    async def get_student_profile(self, student_id: UUID) -> StudentProfile | None:
        return await self.session.scalar(
            select(StudentProfile).options(selectinload(StudentProfile.user)).where(StudentProfile.id == student_id)
        )

    def _enrollment_query(self):
        return select(ClassEnrollment).options(
            selectinload(ClassEnrollment.student).selectinload(StudentProfile.user),
            selectinload(ClassEnrollment.academic_class).selectinload(AcademicClass.branch),
            selectinload(ClassEnrollment.academic_class).selectinload(AcademicClass.cycle),
            selectinload(ClassEnrollment.academic_class).selectinload(AcademicClass.track),
            selectinload(ClassEnrollment.academic_class).selectinload(AcademicClass.level),
        )
