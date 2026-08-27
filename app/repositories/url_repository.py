from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def create(self, url: URL) -> URL:
        self._session.add(url)

        await self._session.flush()

        return url
