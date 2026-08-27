from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.short_code import generate_short_code
from app.models import URL
from app.repositories.url_repository import URLRepository


class URLService:
    MAX_CREATE_RETRIES = 3

    def __init__(
            self,
            session: AsyncSession,
            url_repository: URLRepository,
    ) -> None:
        self._session = session
        self._url_repository = url_repository

    async def create_short_url(
            self,
            original_url: str,
    ) -> URL:
        for _ in range(self.MAX_CREATE_RETRIES):
            url = URL(
                original_url=original_url,
                short_code=generate_short_code(),
            )

            try:
                async with self._session.begin_nested():
                    await self._url_repository.create(url)

            except IntegrityError as exc:
                if not self._is_short_code_collision(exc):
                    raise

                continue

            await self._session.commit()

            return url

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

    @staticmethod
    def _is_short_code_collision(
            exc: IntegrityError,
    ) -> bool:
        return (
                getattr(exc.orig, "sqlstate", None) == "23505"
                and getattr(exc.orig, "constraint_name", None)
                == "uq_urls_short_code"
        )
