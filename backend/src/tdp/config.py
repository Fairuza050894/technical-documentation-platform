from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="TDP_",
        env_file=(".env", "backend/.env"),
        extra="ignore",
    )

    app_name: str = "Technical Documentation Platform"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "staging", "production"] = "development"
    api_prefix: str = "/api"
    allowed_origins: tuple[str, ...] = ("http://127.0.0.1:4173",)
    database_path: Path = Path(".runtime/tdp.sqlite3")
    artifact_root_path: Path = Path(".runtime/artifacts")
    max_source_file_bytes: int = 5 * 1024 * 1024
    auth_mode: Literal["local"] = "local"
    local_identity_subject: str = "local-technical-writer"
    local_identity_name: str = "Technical Writer"
    local_identity_email: str = "technical.writer@local.invalid"

    @model_validator(mode="after")
    def validate_runtime_contract(self) -> Self:
        if not self.api_prefix.startswith("/"):
            raise ValueError("TDP_API_PREFIX must begin with '/'.")
        if self.max_source_file_bytes < 1:
            raise ValueError("TDP_MAX_SOURCE_FILE_BYTES must be greater than zero.")
        if self.auth_mode == "local" and self.environment in {"staging", "production"}:
            raise ValueError(
                "TDP_AUTH_MODE=local is restricted to development and test environments."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
