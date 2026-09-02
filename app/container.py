import logging

from dependency_injector import providers, containers
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import get_settings, Settings
from app.infrastructure.cache.redis_client import RedisCache

logger = logging.getLogger(__name__)


class Container(containers.DeclarativeContainer):
    """
    Main Dependency Injection Container.

    This container:
    1. Creates all dependencies with proper configuration
    2. Wires them together with dependency injection
    3. Manages their lifecycle (initialization and cleanup)
    4. Provides them to the application via FastAPI dependencies

    """

    config = providers.Configuration()

    settings = providers.Singleton(get_settings())

    async_engine = providers.Resource(
        create_async_engine,
        url=providers.Callable(lambda s: s.database_url, settings),
        future=True,
        pool_pre_ping=True,
        pool_size=providers.Callable(lambda s: s.DB_POOL_SIZE, settings),
        max_overflow=providers.Callable(lambda s: s.DB_MAX_OVERFLOW, settings),
        pool_timeout=providers.Callable(lambda s: s.DB_POOL_TIMEOUT, settings),
        pool_recycle=3600,
        connect_args={'statement_cache_size': 0},
    )

    async_session_factory = providers.Singleton(
        async_sessionmaker,
        bind=async_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    redis_cache = providers.Singleton(
        RedisCache,
        redis_url=providers.Callable(lambda s: s.redis_url, settings),
    )

    @staticmethod
    async def shutdown_resources(container: 'Container') -> None:
        """
        Gracefully shutdown all resources.

        Should be called on application shutdown.
        """

        redis_cache = container.redis_cache()
        await redis_cache.close()
        logger.info('Redis cache connection closed')

        async_engine = container.async_engine()
        await async_engine.dispose()
        logger.info('DB engine disposed')


class ContainerManager:
    """Thread-safe singleton wrapper around the DI container."""

    _instance: Container | None = None

    @classmethod
    def get(cls) -> Container:
        if cls._instance is None:
            cls._instance = Container()
        return cls._instance

    @classmethod
    async def create(cls, settings: Settings) -> Container:
        container = cls.get()

        container.settings.override(providers.Object(settings))

        logger.info(f'Container initialized for {settings.APP_NAME} v{settings.VERSION}')

        await Container.init_resources(container)
        return container

    @classmethod
    async def destroy(cls) -> None:
        if cls._instance is not None:
            await Container.shutdown_resources(cls._instance)
            cls._instance = None


def get_container() -> Container:
    return ContainerManager.get()


async def create_container(settings: Settings) -> Container:
    return await ContainerManager.create(settings)


async def destroy_container() -> None:
    return await ContainerManager.destroy()
