from app.infrastructure.cache.redis_connection import RedisConnection


class URLCache:
    """Caching semantics only — key format, TTL policy. Built on top of a live connection."""

    def __init__(self, connection: RedisConnection) -> None:
        self._client = connection.client

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        await self._client.set(key, value, ex=ex)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)