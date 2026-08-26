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

    # --- Auth ---
    auth_mode: Literal["local", "oidc"] = "local"
    local_identity_subject: str = "local-technical-writer"
    local_identity_name: str = "Technical Writer"
    local_identity_email: str = "technical.writer@local.invalid"

    # --- OIDC (1.1.1, 1.1.3) ---
    oidc_issuer: str = ""
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_audience: str = ""  # Defaults to client_id if empty

    # --- Session (1.1.4) ---
    token_blacklist_enabled: bool = True

    # --- Phase 1: Security & Infrastructure ---
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    audit_enabled: bool = True

    # --- HSTS (2.1.4.3) ---
    hsts_enabled: bool = False
    hsts_max_age: int = 31_536_000
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False

    # --- CSRF (4.1.4.2) ---
    csrf_enabled: bool = False
    csrf_cookie_secure: bool = False
    csrf_cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    # --- Authorization (WS 1.2) ---
    rbac_enabled: bool = True
    default_admin_subjects: tuple[str, ...] = ("local-technical-writer",)

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
        if self.auth_mode == "oidc":
            if not self.oidc_issuer:
                raise ValueError("TDP_OIDC_ISSUER is required when auth_mode is 'oidc'.")
            if not self.oidc_client_id:
                raise ValueError("TDP_OIDC_CLIENT_ID is required when auth_mode is 'oidc'.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()