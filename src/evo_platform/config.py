from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EVO_", extra="ignore")

    environment: str = "development"
    service_name: str = "evo-platform"
    database_url: str = Field(default="postgresql+asyncpg://evo:evo@localhost:5432/evo")


@lru_cache
def get_settings() -> Settings:
    return Settings()
