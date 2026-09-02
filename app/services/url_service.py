import json
import secrets
import string

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.cache.url_cache import URLCache
from app.models import URL
from app.repositories.url_repository import URLRepository


class URLService:
    SHORT_CODE_LENGTH = 8
    MAX_CREATE_RETRIES = 3
    CACHE_TTL_SECONDS = 3600

    def __init__(
            self,
            session: AsyncSession,
            url_repository: URLRepository,
            cache: URLCache,
    ) -> None:
        self._session = session
        self._url_repository = url_repository
        self._cache = cache

    async def create_short_url(self, original_url: str) -> URL:
        for _ in range(self.MAX_CREATE_RETRIES):
            candidate = URL(
                original_url=original_url,
                short_code=self._generate_short_code(),
            )
            created = await self._url_repository.try_create(candidate)
            if created is not None:
                await self._session.commit()
                return created

        raise RuntimeError("Failed to generate a unique short code")

    async def get_url_by_short_code(self, short_code: str) -> URL | None:
        """Cached lookup — used only by the redirect path. Never carries visit_count."""
        cache_key = self._cache_key(short_code)
        cached = await self._cache.get(cache_key)

        if cached is not None:
            data = json.loads(cached)
            return URL(
                id=data["id"],
                original_url=data["original_url"],
                short_code=short_code,
            )

        url = await self._url_repository.get_by_short_code(short_code)
        if url is None:
            return None

        await self._cache.set(
            cache_key,
            json.dumps({"id": url.id, "original_url": url.original_url}),
            ex=self.CACHE_TTL_SECONDS,
        )
        return url



    async def get_url_with_stats(self, short_code: str) -> URL | None:
        """Always hits the DB — visit_count must be fresh, never cached."""
        return await self._url_repository.get_visit_count(short_code)

    @staticmethod
    def _cache_key(short_code: str) -> str:
        return f"url:{short_code}"

    @staticmethod
    def _generate_short_code() -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(
            secrets.choice(alphabet)
            for _ in range(URLService.SHORT_CODE_LENGTH)
        )
