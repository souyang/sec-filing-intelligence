from __future__ import annotations

from collections.abc import AsyncIterator

from sec_alphaops_db.session import get_async_session_factory
from sqlalchemy.ext.asyncio import AsyncSession

from sec_alphaops_api.settings import settings

_session_factory = get_async_session_factory(settings.database_url)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with _session_factory() as session:
        yield session
