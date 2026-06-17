from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.domain.enums import MaterialCreatorRole, UserRole
from app.models.material import Material
from app.models.user import User
from app.repositories.academic import AcademicRepository
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.enrollments import EnrollmentRepository
from app.repositories.materials import MaterialRepository
from app.schemas.materials import MaterialCreate, MaterialUpdate


class MaterialService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.academic = AcademicRepository(session)
        self.enrollments = EnrollmentRepository(session)
        self.materials = MaterialRepository(session)
        self.audit_logs = AuditLogRepository(session)

    async def create_material(self, payload: MaterialCreate, actor: User) -> Material:
        academic_class = await self.academic.get_class(payload.class_id)
        if academic_class is None:
            raise AppException("Class not found", HTTPStatus.NOT_FOUND)
        if actor.role == UserRole.admin:
            if payload.creator_id is None:
                raise AppException("creator_id is required for admin-created materials", HTTPStatus.BAD_REQUEST)
            creator = await self.academic.get_teacher_profile(payload.creator_id)
            if creator is None:
                raise AppException("Teacher profile not found", HTTPStatus.NOT_FOUND)
            self._ensure_creator_role_matches_class(payload.creator_id, academic_class, payload.creator_role)
            creator_id = payload.creator_id
        elif actor.role == UserRole.teacher and actor.teacher_profile is not None:
            self._ensure_creator_role_matches_class(actor.teacher_profile.id, academic_class, payload.creator_role)
            creator_id = actor.teacher_profile.id
        else:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        material = Material(
            class_id=payload.class_id,
            creator_id=creator_id,
            creator_role=payload.creator_role,
            title=payload.title,
            description=payload.description,
            material_type=payload.material_type,
            url=str(payload.url),
            is_active=True,
        )
        try:
            await self.materials.add(material)
            await self.audit_logs.add(
                actor.id,
                "create_material",
                "material",
                material.id,
                new_value={"class_id": str(material.class_id), "title": material.title},
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppException("Material data is invalid", HTTPStatus.BAD_REQUEST) from exc
        return await self.get_material_for_user(material.id, actor)

    async def list_materials_for_user(self, actor: User) -> list[Material]:
        if actor.role == UserRole.admin:
            return await self.materials.list_all()
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            classes = await self.academic.list_classes_for_teacher(actor.teacher_profile.id)
            materials: list[Material] = []
            for academic_class in classes:
                materials.extend(await self.materials.list_for_class(academic_class.id))
            return materials
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    async def get_material_for_user(self, material_id: UUID, actor: User) -> Material:
        material = await self.materials.get_by_id(material_id)
        if material is None:
            raise AppException("Material not found", HTTPStatus.NOT_FOUND)
        if actor.role == UserRole.admin:
            return material
        if actor.role == UserRole.teacher and actor.teacher_profile is not None:
            if actor.teacher_profile.id in {material.academic_class.instructor_id, material.academic_class.mentor_id}:
                return material
        raise AppException("Forbidden", HTTPStatus.FORBIDDEN)

    async def update_material(self, material_id: UUID, payload: MaterialUpdate, actor: User) -> Material:
        material = await self.materials.get_by_id(material_id)
        if material is None:
            raise AppException("Material not found", HTTPStatus.NOT_FOUND)
        if actor.role != UserRole.admin:
            if actor.role != UserRole.teacher or actor.teacher_profile is None or material.creator_id != actor.teacher_profile.id:
                raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        update_data = payload.model_dump(exclude_unset=True)
        next_creator_role = update_data.get("creator_role", material.creator_role)
        self._ensure_creator_role_matches_class(material.creator_id, material.academic_class, next_creator_role)
        old_value = {
            "title": material.title,
            "material_type": material.material_type.value,
            "is_active": material.is_active,
        }
        for field, value in update_data.items():
            if field == "url" and value is not None:
                setattr(material, field, str(value))
            else:
                setattr(material, field, value)
        await self.audit_logs.add(
            actor.id,
            "update_material",
            "material",
            material.id,
            old_value=old_value,
            new_value={
                "title": material.title,
                "material_type": material.material_type.value,
                "is_active": material.is_active,
            },
        )
        await self.session.commit()
        return await self.get_material_for_user(material.id, actor)

    async def delete_material(self, material_id: UUID, actor: User) -> None:
        material = await self.materials.get_by_id(material_id)
        if material is None:
            raise AppException("Material not found", HTTPStatus.NOT_FOUND)
        if actor.role != UserRole.admin:
            if actor.role != UserRole.teacher or actor.teacher_profile is None or material.creator_id != actor.teacher_profile.id:
                raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        material.deleted_at = datetime.now(UTC)
        await self.audit_logs.add(actor.id, "delete_material", "material", material.id)
        await self.session.commit()

    async def list_materials_for_teacher_class(self, class_id: UUID, actor: User) -> list[Material]:
        academic_class = await self.academic.get_class(class_id)
        if academic_class is None:
            raise AppException("Class not found", HTTPStatus.NOT_FOUND)
        if actor.role != UserRole.teacher or actor.teacher_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        if actor.teacher_profile.id not in {academic_class.instructor_id, academic_class.mentor_id}:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        return await self.materials.list_for_class(class_id)

    async def list_materials_for_student_active_class(self, actor: User) -> list[Material]:
        if actor.role != UserRole.student or actor.student_profile is None:
            raise AppException("Forbidden", HTTPStatus.FORBIDDEN)
        enrollment = await self.enrollments.get_active_for_student(actor.student_profile.id)
        if enrollment is None:
            raise AppException("Active class not found", HTTPStatus.NOT_FOUND)
        return await self.materials.list_for_class(enrollment.class_id, active_only=True)

    def _ensure_creator_role_matches_class(
        self,
        teacher_profile_id: UUID,
        academic_class,
        creator_role: MaterialCreatorRole,
    ) -> None:
        can_use_instructor = academic_class.instructor_id == teacher_profile_id
        can_use_mentor = academic_class.mentor_id == teacher_profile_id
        if creator_role == MaterialCreatorRole.instructor and not can_use_instructor:
            raise AppException("Teacher is not assigned as instructor for this class", HTTPStatus.FORBIDDEN)
        if creator_role == MaterialCreatorRole.mentor and not can_use_mentor:
            raise AppException("Teacher is not assigned as mentor for this class", HTTPStatus.FORBIDDEN)
