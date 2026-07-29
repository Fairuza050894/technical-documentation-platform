from pathlib import Path

from fastapi.testclient import TestClient

from tdp.config import Settings
from tdp.main import create_app


def build_client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                database_path=tmp_path / "api.sqlite3",
                artifact_root_path=tmp_path / "artifacts",
            )
        )
    )


def create_project(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/projects",
        json={
            "key": "DOCS",
            "name": "Documentation Platform",
            "description": "",
            "workspace_type": "PERSONAL",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_import_list_and_archive_openapi_source(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    content = b"""openapi: 3.1.0
info:
  title: Commerce API
  version: 1.0.0
paths:
  /orders:
    get: {}
    post: {}
"""

    create_response = client.post(
        f"/api/projects/{project['id']}/sources/openapi",
        data={"name": "Commerce OpenAPI"},
        files={"file": ("commerce.yaml", content, "application/yaml")},
    )

    assert create_response.status_code == 201
    source = create_response.json()
    assert source["api_title"] == "Commerce API"
    assert source["operation_count"] == 2
    assert source["status"] == "READY"

    list_response = client.get(f"/api/projects/{project['id']}/sources")
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    artifact_path = tmp_path / "artifacts" / source["id"] / "source.yaml"
    assert artifact_path.read_bytes() == content

    archive_response = client.post(f"/api/sources/{source['id']}/archive")
    assert archive_response.status_code == 200
    assert archive_response.json()["status"] == "ARCHIVED"


def test_invalid_openapi_uses_standard_error_response(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)

    response = client.post(
        f"/api/projects/{project['id']}/sources/openapi",
        data={"name": "Invalid specification"},
        files={"file": ("invalid.json", b'{"openapi":"3.1.0"}', "application/json")},
        headers={"X-Request-ID": "source-validation-001"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_OPENAPI_DOCUMENT"
    assert response.json()["error"]["requestId"] == "source-validation-001"


def test_archived_project_rejects_source_import(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    assert client.post(f"/api/projects/{project['id']}/archive").status_code == 200

    response = client.post(
        f"/api/projects/{project['id']}/sources/openapi",
        data={"name": "Commerce OpenAPI"},
        files={
            "file": (
                "commerce.yaml",
                b"openapi: 3.1.0\ninfo:\n  title: API\n  version: 1.0.0\npaths: {}\n",
                "application/yaml",
            )
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SOURCE_PROJECT_ARCHIVED"
