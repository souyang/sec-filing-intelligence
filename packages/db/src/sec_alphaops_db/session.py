from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@lru_cache(maxsize=2)
def _engine(url: str):
    return create_async_engine(url, pool_size=10, max_overflow=5)


def get_async_session_factory(database_url: str | None = None) -> async_sessionmaker[AsyncSession]:
    from sec_alphaops_db.migrate import normalize_database_url

    url = normalize_database_url(
        database_url
        or os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://alphaops:alphaops@localhost:5432/alphaops",
        )
    )
    return async_sessionmaker(_engine(url), expire_on_commit=False)
