from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.cache.redis_connection import RedisConnection
from app.infrastructure.cache.url_cache import URLCache
from app.infrastructure.database.session import (
    get_db_session,
    get_session_factory,
)
from app.repositories.url_repository import URLRepository
from app.services.url_service import URLService
from app.services.visit_service import VisitService


def get_redis_connection(request: Request) -> RedisConnection:
    return request.app.state.redis_connection


def get_url_cache(
        connection: Annotated[RedisConnection, Depends(get_redis_connection)],
) -> URLCache:
    return URLCache(connection)


async def get_url_service(
        session: Annotated[AsyncSession, Depends(get_db_session)],
        cache: Annotated[URLCache, Depends(get_url_cache)],
) -> URLService:
    return URLService(
        session=session,
        url_repository=URLRepository(session),
        cache=cache,
    )


async def get_visit_service(
        session: Annotated[
            AsyncSession,
            Depends(get_db_session),
        ],
        session_factory: Annotated[
            async_sessionmaker[AsyncSession],
            Depends(get_session_factory),
        ],
) -> VisitService:
    return VisitService(
        session=session,
        session_factory=session_factory,
    )
