from pathlib import Path

from fastapi.testclient import TestClient

from tdp.config import Settings
from tdp.main import create_app


def build_client(database_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                database_path=database_path,
                artifact_root_path=database_path.parent / "artifacts",
            )
        )
    )


def test_health_endpoint_returns_service_metadata(tmp_path: Path) -> None:
    client = build_client(tmp_path / "health.sqlite3")

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Technical Documentation Platform",
        "version": "0.1.0",
        "environment": "development",
    }
    assert response.headers["X-Request-ID"]


def test_health_endpoint_preserves_supplied_request_id(tmp_path: Path) -> None:
    client = build_client(tmp_path / "health.sqlite3")

    response = client.get("/api/health", headers={"X-Request-ID": "audit-request-001"})

    assert response.headers["X-Request-ID"] == "audit-request-001"


def test_liveness_alias_returns_service_metadata(tmp_path: Path) -> None:
    client = build_client(tmp_path / "health.sqlite3")

    response = client.get("/api/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_checks_database_and_artifact_store(tmp_path: Path) -> None:
    client = build_client(tmp_path / "health.sqlite3")

    response = client.get("/api/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["dependencies"]["database"]["status"] == "ready"
    assert response.json()["dependencies"]["artifact_store"]["status"] == "ready"
