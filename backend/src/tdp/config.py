from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="TDP_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "Technical Documentation Platform"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_prefix: str = "/api"
    allowed_origins: tuple[str, ...] = ("http://127.0.0.1:4173",)
    database_path: Path = Path(".runtime/tdp.sqlite3")


@lru_cache
def get_settings() -> Settings:
    return Settings()
