from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.middleware import RequestLoggingMiddleware
from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.infrastructure.cache.redis_connection import RedisConnection


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    redis_connection = RedisConnection(
        redis_url=settings.redis_url,
        max_connections=settings.redis_pool_size,
    )
    await redis_connection.connect()
    app.state.redis_connection = redis_connection

    yield

    await redis_connection.close()


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        lifespan=lifespan,
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(api_router)

    return app


app = create_app()