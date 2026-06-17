import asyncio
from collections.abc import AsyncGenerator

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.db.session import AsyncSessionLocal, engine
from app.main import app
from app.seed import seed_all


@pytest.fixture(scope="session", autouse=True)
def migrate_database() -> None:
    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(alembic_config, "head")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def reset_database() -> AsyncGenerator[None, None]:
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "TRUNCATE audit_logs, refresh_tokens, notifications, final_projects, progress_snapshots, quiz_results, quizzes, attendance_records, attendance_sessions, grade_entries, assignment_submissions, assignments, materials, class_enrollments, classes, levels, branches, cycles, tracks, "
                    "admin_profiles, teacher_profiles, student_profiles, users RESTART IDENTITY CASCADE"
                )
            )
    except (ConnectionError, OSError, OperationalError) as exc:
        if settings.environment == "test":
            raise
        pytest.skip(f"PostgreSQL is not available: {exc}")
    await seed_all()
    yield
    async with AsyncSessionLocal() as session:
        await session.rollback()
    await engine.dispose()


@pytest.fixture
async def client(reset_database: None) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.fixture
async def public_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.fixture
async def admin_tokens(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/auth/login",
        json={"email": "admin@ica.eg", "password": "Admin@123456"},
    )
    assert response.status_code == 200
    return response.json()["data"]


@pytest.fixture
def admin_headers(admin_tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_tokens['access_token']}"}
