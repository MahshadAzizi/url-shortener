from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.short_code import generate_short_code
from app.models.url import URL
from app.models.visit import Visit
from app.repositories.url_repository import URLRepository
from app.repositories.visit_repository import VisitRepository


class URLService:
    MAX_CREATE_RETRIES = 3

    def __init__(
            self,
            session: AsyncSession,
            url_repository: URLRepository,
            visit_repository: VisitRepository,
    ) -> None:
        self._session = session
        self._url_repository = url_repository
        self._visit_repository = visit_repository

    async def create_short_url(
            self,
            original_url: str,
    ) -> URL:
        for _ in range(self.MAX_CREATE_RETRIES):
            short_code = generate_short_code()

            url = URL(
                original_url=original_url,
                short_code=short_code,
            )

            try:
                async with self._session.begin_nested():
                    await self._url_repository.create(url)

                await self._session.commit()

                return url

            except IntegrityError:
                continue

        raise RuntimeError(
            "Failed to generate a unique short code"
        )

    async def get_url_by_short_code(
            self,
            short_code: str,
    ) -> URL | None:
        return await self._url_repository.get_by_short_code(
            short_code,
        )

    async def record_visit(
            self,
            url_id: int,
            ip_address: str | None,
    ) -> None:
        visit = Visit(
            url_id=url_id,
            ip_address=ip_address,
        )

        await self._visit_repository.create(visit)

        await self._session.commit()

    async def get_visit_count(
            self,
            url_id: int,
    ) -> int:
        return await self._visit_repository.count_by_url_id(
            url_id,
        )
