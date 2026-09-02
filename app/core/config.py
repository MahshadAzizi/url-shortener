from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    app_name: str = "URL Shortener"
    version: str = "0.1.0"

    debug: bool = False
    environment: str = "development"

    api_v1_prefix: str = "/api/v1"

    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int = 5432
    postgres_db: str

    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=5, ge=0)
    db_pool_timeout: int = Field(default=30, ge=1)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    # --- Redis Config ---
    redis_host: str = Field(default='localhost', description='Redis host')
    redis_port: int = Field(default=6379, description='Redis port')
    redis_db: int = Field(default=0, description='Redis database number')
    redis_password: str | None = Field(default=None, description='Redis password (optional)')
    redis_pool_size: int = Field(default=50, description='Maximum Redis connection pool size')

    @property
    def redis_url(self) -> str:
        auth = f':{self.redis_password}@' if self.redis_password else ''
        return f'redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}'


@lru_cache
def get_settings() -> Settings:
    return Settings()
