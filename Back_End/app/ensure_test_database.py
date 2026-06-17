import asyncio
import re

import asyncpg
from sqlalchemy.engine import make_url

from app.core.config import settings


def quote_identifier(identifier: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
        raise ValueError("Database name must be a simple SQL identifier")
    return f'"{identifier}"'


async def ensure_test_database() -> None:
    url = make_url(settings.database_url)
    target_database = url.database
    if target_database is None:
        raise ValueError("DATABASE_URL must include a database name")

    maintenance_database = "postgres"
    connection = await asyncpg.connect(
        user=url.username,
        password=url.password,
        host=url.host,
        port=url.port or 5432,
        database=maintenance_database,
    )
    try:
        exists = await connection.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", target_database)
        if not exists:
            await connection.execute(f"CREATE DATABASE {quote_identifier(target_database)}")
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(ensure_test_database())

