from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.middleware import RequestLoggingMiddleware
from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(api_router)

    return app


app = create_app()
