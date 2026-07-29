from pathlib import Path

from fastapi.testclient import TestClient

from tdp.config import Settings
from tdp.main import create_app


def build_client(database_path: Path) -> TestClient:
    return TestClient(create_app(Settings(database_path=database_path)))


def test_create_list_and_archive_project(tmp_path: Path) -> None:
    client = build_client(tmp_path / "api.sqlite3")

    create_response = client.post(
        "/api/projects",
        json={
            "key": "docs",
            "name": "Documentation Platform",
            "description": "Source-backed technical documentation",
            "workspace_type": "PERSONAL",
        },
    )

    assert create_response.status_code == 201
    project = create_response.json()
    assert project["key"] == "DOCS"
    assert project["status"] == "ACTIVE"

    list_response = client.get("/api/projects")
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    archive_response = client.post(f"/api/projects/{project['id']}/archive")
    assert archive_response.status_code == 200
    assert archive_response.json()["status"] == "ARCHIVED"


def test_duplicate_key_uses_standard_error_response(tmp_path: Path) -> None:
    client = build_client(tmp_path / "api.sqlite3")
    payload = {
        "key": "DOCS",
        "name": "Documentation Platform",
        "description": "",
        "workspace_type": "PERSONAL",
    }

    assert client.post("/api/projects", json=payload).status_code == 201
    response = client.post("/api/projects", json=payload)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PROJECT_KEY_ALREADY_EXISTS"
    assert response.json()["error"]["requestId"]


def test_invalid_payload_uses_standard_error_response(tmp_path: Path) -> None:
    client = build_client(tmp_path / "api.sqlite3")

    response = client.post(
        "/api/projects",
        json={
            "key": "invalid key",
            "name": "No",
            "description": "",
            "workspace_type": "PERSONAL",
        },
        headers={"X-Request-ID": "validation-001"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    assert response.json()["error"]["requestId"] == "validation-001"
    assert response.json()["error"]["details"]
