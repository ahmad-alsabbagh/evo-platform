from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EVO_", extra="ignore")

    environment: str = "development"
    service_name: str = "evo-platform"
    database_url: str = Field(default="postgresql+asyncpg://evo:evo@localhost:5432/evo")
    redis_url: str = "redis://localhost:6379/0"
    redis_stream: str = "evo:evaluation"
    redis_group: str = "evo-workers"
    redis_visibility_timeout_ms: int = Field(default=60_000, ge=1_000)


@lru_cache
def get_settings() -> Settings:
    return Settings()
