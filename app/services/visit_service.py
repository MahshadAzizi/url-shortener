from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.visit import Visit
from app.repositories.visit_repository import VisitRepository


class VisitService:
    def __init__(
            self,
            session: AsyncSession,
            session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._repository = VisitRepository(session)
        self._session_factory = session_factory

    async def record_visit(
            self,
            url_id: int,
            ip_address: str | None,
    ) -> None:
        async with self._session_factory() as session:
            repository = VisitRepository(session)

            visit = Visit(
                url_id=url_id,
                ip_address=ip_address,
            )

            await repository.create(visit)

            await session.commit()

    async def get_visit_count(
            self,
            url_id: int,
    ) -> int:
        return await self._repository.count_by_url_id(url_id)
