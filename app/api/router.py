from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.urls import router as url_router
from app.api.routes.redirect import router as redirect_router
from app.core.config import get_settings

settings = get_settings()

api_router = APIRouter()

api_router.include_router(
    health_router,
    tags=["health"],
)

api_router.include_router(
    url_router,
    tags=["urls"],
)

api_router.include_router(
    redirect_router,
    tags=["redirect"],
)
