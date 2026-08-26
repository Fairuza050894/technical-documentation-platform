"""Tests for Phase 1 config additions."""
from __future__ import annotations

from tdp.config import Settings


class TestPhase1Config:
    def test_rate_limit_defaults(self) -> None:
        s = Settings(
            environment="development",
            database_path="/tmp/test.sqlite3",
            artifact_root_path="/tmp/artifacts",
        )
        assert s.rate_limit_enabled is True
        assert s.rate_limit_requests_per_minute == 60

    def test_audit_default_enabled(self) -> None:
        s = Settings(
            environment="development",
            database_path="/tmp/test.sqlite3",
            artifact_root_path="/tmp/artifacts",
        )
        assert s.audit_enabled is True

    def test_oidc_defaults_empty(self) -> None:
        s = Settings(
            environment="development",
            database_path="/tmp/test.sqlite3",
            artifact_root_path="/tmp/artifacts",
        )
        assert s.oidc_issuer == ""
        assert s.oidc_client_id == ""
        assert s.oidc_client_secret == ""

    def test_database_url_default_empty(self) -> None:
        s = Settings(
            environment="development",
            database_path="/tmp/test.sqlite3",
            artifact_root_path="/tmp/artifacts",
        )
        assert s.database_url == ""
