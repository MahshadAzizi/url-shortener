from __future__ import annotations

import logging
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisConnection:
    """Owns the connection pool lifecycle only. Exposes the raw client for anything built on top (cache, streams)."""

    def __init__(self, redis_url: str, max_connections: int = 50) -> None:
        self._redis_url = redis_url
        self._max_connections = max_connections
        self._pool: redis.ConnectionPool | None = None
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        if self._client is not None:
            return
        self._pool = redis.ConnectionPool.from_url(
            self._redis_url,
            decode_responses=True,
            max_connections=self._max_connections,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        self._client = redis.Redis(connection_pool=self._pool)
        await self._client.ping()
        logger.info("Connected to Redis")

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None
        if self._pool is not None:
            await self._pool.disconnect()
            self._pool = None
        logger.info("Redis connection closed")

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            raise RuntimeError("Redis is not connected")
        return self._client
