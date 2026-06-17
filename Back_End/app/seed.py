import asyncio
from datetime import date

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.domain.enums import CycleStatus, UserRole
from app.repositories.academic import AcademicRepository
from app.repositories.users import UserRepository
from app.schemas.academic import BranchCreate, CycleCreate, LevelCreate, TrackCreate
from app.schemas.users import AdminProfileCreate, UserCreate
from app.services.academic import AcademicService
from app.services.users import UserService


async def seed_default_admin() -> None:
    async with AsyncSessionLocal() as session:
        users = UserRepository(session)
        existing_admin = await users.get_by_email(settings.default_admin_email, include_deleted=True)
        if existing_admin is not None:
            return
        await UserService(session).create_user(
            UserCreate(
                email=settings.default_admin_email,
                password=settings.default_admin_password,
                role=UserRole.admin,
                admin_profile=AdminProfileCreate(full_name="Default Admin"),
            )
        )


async def seed_academic_structure() -> None:
    async with AsyncSessionLocal() as session:
        academic = AcademicRepository(session)
        service = AcademicService(session)
        if await academic.get_branch_by_name("Main Branch", include_deleted=True) is None:
            await service.create_branch(BranchCreate(name="Main Branch"), actor=None)
        if await academic.get_cycle_by_number(1, include_deleted=True) is None:
            await service.create_cycle(
                CycleCreate(
                    cycle_number=1,
                    name="Cycle 1",
                    start_date=date(2026, 1, 1),
                    end_date=date(2026, 12, 31),
                    status=CycleStatus.active,
                ),
                actor=None,
            )
        for code, name, track_number in (("BE", "Backend", 14), ("FE", "Frontend", 13)):
            track = await academic.get_track_by_code(code, include_deleted=True)
            if track is None:
                track = await service.create_track(
                    TrackCreate(code=code, name=name, track_number=track_number, create_default_levels=True),
                    actor=None,
                )
            for level_number in (1, 2, 3):
                existing_level = await academic.get_level_by_track_and_number(track.id, level_number, True)
                if existing_level is None:
                    await service.create_level(
                        LevelCreate(
                            track_id=track.id,
                            level_number=level_number,
                            title=f"{track.name} Level {level_number}",
                            duration_months=2,
                        ),
                        actor=None,
                    )


async def seed_all() -> None:
    await seed_default_admin()
    await seed_academic_structure()


if __name__ == "__main__":
    asyncio.run(seed_all())
