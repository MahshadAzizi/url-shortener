from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.url import URL


class URLRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_short_code(
            self,
            short_code: str,
    ) -> URL | None:
        statement = (
            select(URL)
            .where(URL.short_code == short_code)
        )

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def try_create(self, url: URL) -> URL | None:
        """Insert if short_code is free, otherwise return None. Single round-trip, no exception handling needed."""
        stmt = (
            pg_insert(URL)
            .values(
                original_url=url.original_url,
                short_code=url.short_code,
            )
            .on_conflict_do_nothing(index_elements=["short_code"])
            .returning(URL)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def increment_visit_count(self, url_id: int) -> None:
        stmt = (
            update(URL)
            .where(URL.id == url_id)
            .values(visit_count=URL.visit_count + 1)
        )
        await self._session.execute(stmt)

    async def get_visit_count(
            self,
            short_code: str,
    ) -> int | None:
        stmt = (
            select(URL.visit_count)
            .where(URL.short_code == short_code)
        )

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
