from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import (
    get_db_session,
    session_factory,
)
from app.repositories.url_repository import URLRepository
from app.repositories.visit_repository import VisitRepository
from app.services.url_service import URLService
from app.services.visit_service import VisitService


def get_url_service(
        session: Annotated[
            AsyncSession,
            Depends(get_db_session),
        ],
) -> URLService:
    return URLService(
        session=session,
        url_repository=URLRepository(session),
        visit_repository=VisitRepository(session),
    )


def get_visit_service() -> VisitService:
    return VisitService(
        session_factory=session_factory,
    )
