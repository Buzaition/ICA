from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.responses import success_response
from app.db.session import get_session
from app.models.user import User
from app.schemas.materials import MaterialCreate, MaterialRead, MaterialUpdate
from app.services.materials import MaterialService

materials_router = APIRouter()
teacher_materials_router = APIRouter()
student_materials_router = APIRouter()


@materials_router.post("")
async def create_material(
    payload: MaterialCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    material = await MaterialService(session).create_material(payload, current_user)
    return success_response(data=MaterialRead.from_model(material).model_dump(mode="json"))


@materials_router.get("")
async def list_materials(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    materials = await MaterialService(session).list_materials_for_user(current_user)
    return success_response(data=[MaterialRead.from_model(material).model_dump(mode="json") for material in materials])


@materials_router.get("/{material_id}")
async def get_material(
    material_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    material = await MaterialService(session).get_material_for_user(material_id, current_user)
    return success_response(data=MaterialRead.from_model(material).model_dump(mode="json"))


@materials_router.put("/{material_id}")
async def update_material(
    material_id: UUID,
    payload: MaterialUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    material = await MaterialService(session).update_material(material_id, payload, current_user)
    return success_response(data=MaterialRead.from_model(material).model_dump(mode="json"))


@materials_router.delete("/{material_id}")
async def delete_material(
    material_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await MaterialService(session).delete_material(material_id, current_user)
    return success_response()


@teacher_materials_router.get("/me/classes/{class_id}/materials")
async def list_my_class_materials(
    class_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    materials = await MaterialService(session).list_materials_for_teacher_class(class_id, current_user)
    return success_response(data=[MaterialRead.from_model(material).model_dump(mode="json") for material in materials])


@student_materials_router.get("/me/materials")
async def list_my_materials(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    materials = await MaterialService(session).list_materials_for_student_active_class(current_user)
    return success_response(data=[MaterialRead.from_model(material).model_dump(mode="json") for material in materials])
