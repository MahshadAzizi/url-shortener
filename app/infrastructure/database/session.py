from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.database.engine import engine


SessionFactory = async_sessionmaker[AsyncSession]

_session_factory: SessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        yield session


def get_session_factory() -> SessionFactory:
    return _session_factory