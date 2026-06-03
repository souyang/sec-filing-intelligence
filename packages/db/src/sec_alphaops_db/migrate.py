from __future__ import annotations

import asyncio
import os

from sqlalchemy.ext.asyncio import create_async_engine

from sec_alphaops_db.models import Base


def normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


async def run_migrations() -> None:
    url = normalize_database_url(
        os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://alphaops:alphaops@localhost:5432/alphaops",
        )
    )
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Database schema is up to date.")


def main() -> None:
    asyncio.run(run_migrations())


if __name__ == "__main__":
    main()
