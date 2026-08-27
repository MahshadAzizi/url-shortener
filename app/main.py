from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.api.router import api_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
    )
    app.include_router(api_router)

    return app


app = create_app()
