from uuid import UUID

from datetime import datetime
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.enums import GradeCategory
from app.models.academic import Class as AcademicClass
from app.models.grade import GradeEntry
from app.models.profiles import StudentProfile


class GradeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, grade_entry: GradeEntry) -> GradeEntry:
        self.session.add(grade_entry)
        await self.session.flush()
        await self.session.refresh(grade_entry)
        return grade_entry

    async def get_by_id(self, grade_entry_id: UUID, include_deleted: bool = False) -> GradeEntry | None:
        statement = self._grade_query().where(GradeEntry.id == grade_entry_id)
        if not include_deleted:
            statement = statement.where(GradeEntry.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def get_by_assignment_submission_id(self, submission_id: UUID) -> GradeEntry | None:
        return await self.session.scalar(
            self._grade_query().where(
                GradeEntry.assignment_submission_id == submission_id,
                GradeEntry.deleted_at.is_(None),
            )
        )

    async def list_all(self) -> list[GradeEntry]:
        result = await self.session.scalars(
            self._grade_query().where(GradeEntry.deleted_at.is_(None)).order_by(GradeEntry.created_at.desc())
        )
        return list(result.all())

    async def list_for_class(self, class_id: UUID) -> list[GradeEntry]:
        result = await self.session.scalars(
            self._grade_query()
            .where(GradeEntry.class_id == class_id, GradeEntry.deleted_at.is_(None))
            .order_by(GradeEntry.created_at.desc())
        )
        return list(result.all())

    async def list_for_student(self, student_id: UUID) -> list[GradeEntry]:
        result = await self.session.scalars(
            self._grade_query()
            .where(GradeEntry.student_id == student_id, GradeEntry.deleted_at.is_(None))
            .order_by(GradeEntry.created_at.desc())
        )
        return list(result.all())

    async def list_for_teacher(self, teacher_profile_id: UUID) -> list[GradeEntry]:
        result = await self.session.scalars(
            self._grade_query()
            .join(GradeEntry.academic_class)
            .where(
                GradeEntry.deleted_at.is_(None),
                or_(AcademicClass.instructor_id == teacher_profile_id, AcademicClass.mentor_id == teacher_profile_id),
            )
            .order_by(GradeEntry.created_at.desc())
        )
        return list(result.all())

    async def list_bonus_all(self) -> list[GradeEntry]:
        result = await self.session.scalars(
            self._grade_query()
            .where(GradeEntry.category == GradeCategory.bonus, GradeEntry.deleted_at.is_(None))
            .order_by(GradeEntry.created_at.desc())
        )
        return list(result.all())

    async def list_bonus_for_student(self, student_id: UUID) -> list[GradeEntry]:
        result = await self.session.scalars(
            self._grade_query()
            .where(
                GradeEntry.category == GradeCategory.bonus,
                GradeEntry.student_id == student_id,
                GradeEntry.deleted_at.is_(None),
            )
            .order_by(GradeEntry.created_at.desc())
        )
        return list(result.all())

    async def list_bonus_for_class(self, class_id: UUID) -> list[GradeEntry]:
        result = await self.session.scalars(
            self._grade_query()
            .where(
                GradeEntry.category == GradeCategory.bonus,
                GradeEntry.class_id == class_id,
                GradeEntry.deleted_at.is_(None),
            )
            .order_by(GradeEntry.created_at.desc())
        )
        return list(result.all())

    async def list_bonus_for_teacher(self, teacher_profile_id: UUID) -> list[GradeEntry]:
        result = await self.session.scalars(
            self._grade_query()
            .join(GradeEntry.academic_class)
            .where(
                GradeEntry.category == GradeCategory.bonus,
                GradeEntry.deleted_at.is_(None),
                or_(AcademicClass.instructor_id == teacher_profile_id, AcademicClass.mentor_id == teacher_profile_id),
            )
            .order_by(GradeEntry.created_at.desc())
        )
        return list(result.all())

    async def count_bonus_for_student_class_between(
        self,
        student_id: UUID,
        class_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> int:
        result = await self.session.scalars(
            select(GradeEntry.id).where(
                and_(
                    GradeEntry.category == GradeCategory.bonus,
                    GradeEntry.student_id == student_id,
                    GradeEntry.class_id == class_id,
                    GradeEntry.deleted_at.is_(None),
                    GradeEntry.created_at >= start_at,
                    GradeEntry.created_at < end_at,
                )
            )
        )
        return len(result.all())

    async def list_corrections_for_entry(self, grade_entry_id: UUID) -> list[GradeEntry]:
        result = await self.session.scalars(
            self._grade_query()
            .where(
                GradeEntry.related_entry_id == grade_entry_id,
                GradeEntry.category == GradeCategory.correction,
                GradeEntry.deleted_at.is_(None),
            )
            .order_by(GradeEntry.created_at.desc())
        )
        return list(result.all())

    async def list_corrections_all(self) -> list[GradeEntry]:
        result = await self.session.scalars(
            self._grade_query()
            .where(GradeEntry.category == GradeCategory.correction, GradeEntry.deleted_at.is_(None))
            .order_by(GradeEntry.created_at.desc())
        )
        return list(result.all())

    async def list_corrections_for_teacher(self, teacher_profile_id: UUID) -> list[GradeEntry]:
        result = await self.session.scalars(
            self._grade_query()
            .join(GradeEntry.academic_class)
            .where(
                GradeEntry.category == GradeCategory.correction,
                GradeEntry.deleted_at.is_(None),
                or_(AcademicClass.instructor_id == teacher_profile_id, AcademicClass.mentor_id == teacher_profile_id),
            )
            .order_by(GradeEntry.created_at.desc())
        )
        return list(result.all())

    def _grade_query(self):
        return select(GradeEntry).options(
            selectinload(GradeEntry.student).selectinload(StudentProfile.user),
            selectinload(GradeEntry.academic_class).selectinload(AcademicClass.branch),
            selectinload(GradeEntry.academic_class).selectinload(AcademicClass.cycle),
            selectinload(GradeEntry.academic_class).selectinload(AcademicClass.track),
            selectinload(GradeEntry.academic_class).selectinload(AcademicClass.level),
            selectinload(GradeEntry.teacher),
            selectinload(GradeEntry.related_entry),
            selectinload(GradeEntry.assignment_submission),
            selectinload(GradeEntry.created_by_user),
        )
