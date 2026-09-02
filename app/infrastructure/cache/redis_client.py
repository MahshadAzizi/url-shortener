from __future__ import annotations

import logging
import redis.asyncio as aioredis
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Provides async Redis operations for caching.
    Handles connection pooling and error recovery.
    """

    def __init__(
            self,
            redis_url: str | None,
            decode_responses: bool = True,
            max_connections: int = 50,
    ):
        """
        Initialize Redis cache adapter.

        Args:
            redis_url: Redis url (defaults to settings)
            decode_responses: Automatically decode responses to strings
            max_connections: Maximum number of connections in pool
        """
        self.redis_url = redis_url or get_settings.redis_url
        self.decode_responses = decode_responses
        self.max_connections = max_connections

        self._client: aioredis.Redis | None = None
        self._connection_pool: aioredis.ConnectionPool | None = None

    async def connect(self) -> None:
        """Establish Redis connection pool."""
        if self._client is not None:
            return
        try:
            self._connection_pool = aioredis.ConnectionPool.from_url(
                url=self.redis_url,
                decode_responses=True,
                max_connections=self.max_connections,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            self._client = aioredis.Redis(connection_pool=self._connection_pool)
            await self._client.ping()
            logger.info(f'Connected to Redis at {self.redis_url})')

        except Exception as e:
            logger.error(f'Failed to connect to Redis: {e}', exc_info=True)
            raise

    async def close(self) -> None:
        """Close Redis connection and cleanup."""
        if self._client:
            await self._client.close()
            self._client = None

        if self._connection_pool:
            await self._connection_pool.disconnect()
            self._connection_pool = None

        logger.info('Redis connection closed')
