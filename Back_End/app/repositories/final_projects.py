from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.academic import Class as AcademicClass
from app.models.final_project import FinalProject
from app.models.profiles import StudentProfile


class FinalProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, final_project: FinalProject) -> FinalProject:
        self.session.add(final_project)
        await self.session.flush()
        await self.session.refresh(final_project)
        return final_project

    async def get_by_id(self, final_project_id: UUID, include_deleted: bool = False) -> FinalProject | None:
        statement = self._query().where(FinalProject.id == final_project_id)
        if not include_deleted:
            statement = statement.where(FinalProject.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def get_for_student_class_level(
        self,
        student_id: UUID,
        class_id: UUID,
        level_id: UUID,
        include_deleted: bool = False,
    ) -> FinalProject | None:
        statement = self._query().where(
            FinalProject.student_id == student_id,
            FinalProject.class_id == class_id,
            FinalProject.level_id == level_id,
        )
        if not include_deleted:
            statement = statement.where(FinalProject.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def get_for_student_active_class(self, student_id: UUID, class_id: UUID) -> FinalProject | None:
        return await self.session.scalar(
            self._query().where(
                FinalProject.student_id == student_id,
                FinalProject.class_id == class_id,
                FinalProject.deleted_at.is_(None),
            )
        )

    async def list_all(self) -> list[FinalProject]:
        result = await self.session.scalars(
            self._query().where(FinalProject.deleted_at.is_(None)).order_by(FinalProject.submitted_at.desc())
        )
        return list(result.all())

    async def list_for_class(self, class_id: UUID) -> list[FinalProject]:
        result = await self.session.scalars(
            self._query()
            .where(FinalProject.class_id == class_id, FinalProject.deleted_at.is_(None))
            .order_by(FinalProject.submitted_at.desc())
        )
        return list(result.all())

    def _query(self):
        return select(FinalProject).options(
            selectinload(FinalProject.student).selectinload(StudentProfile.user),
            selectinload(FinalProject.academic_class).selectinload(AcademicClass.level),
            selectinload(FinalProject.level),
            selectinload(FinalProject.reviewed_by_admin),
        ).execution_options(populate_existing=True)
