from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.academic import Class as AcademicClass
from app.models.material import Material


class MaterialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, material: Material) -> Material:
        self.session.add(material)
        await self.session.flush()
        await self.session.refresh(material)
        return material

    async def get_by_id(self, material_id: UUID, include_deleted: bool = False) -> Material | None:
        statement = self._material_query().where(Material.id == material_id)
        if not include_deleted:
            statement = statement.where(Material.deleted_at.is_(None))
        return await self.session.scalar(statement)

    async def list_all(self) -> list[Material]:
        result = await self.session.scalars(
            self._material_query().where(Material.deleted_at.is_(None)).order_by(Material.created_at.desc())
        )
        return list(result.all())

    async def list_for_class(self, class_id: UUID, active_only: bool = False) -> list[Material]:
        statement = (
            self._material_query()
            .where(Material.class_id == class_id, Material.deleted_at.is_(None))
            .order_by(Material.created_at.desc())
        )
        if active_only:
            statement = statement.where(Material.is_active.is_(True))
        result = await self.session.scalars(statement)
        return list(result.all())

    def _material_query(self):
        return select(Material).options(
            selectinload(Material.creator),
            selectinload(Material.academic_class).selectinload(AcademicClass.branch),
            selectinload(Material.academic_class).selectinload(AcademicClass.cycle),
            selectinload(Material.academic_class).selectinload(AcademicClass.track),
            selectinload(Material.academic_class).selectinload(AcademicClass.level),
        )
