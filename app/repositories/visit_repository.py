from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.visit import Visit


class VisitRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, visit: Visit) -> Visit:
        self._session.add(visit)
        await self._session.flush()
        return visit

    async def count_by_url_id(self, url_id: int) -> int:
        statement = (
            select(func.count())
            .select_from(Visit)
            .where(Visit.url_id == url_id)
        )

        result = await self._session.execute(statement)

        return result.scalar_one()
