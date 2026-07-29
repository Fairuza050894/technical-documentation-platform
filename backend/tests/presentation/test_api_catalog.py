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


def test_synchronize_source_and_read_api_catalog(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project_response = client.post(
        "/api/projects",
        json={
            "key": "DOCS",
            "name": "Documentation Platform",
            "description": "",
            "workspace_type": "PERSONAL",
        },
    )
    project_id = str(project_response.json()["id"])

    source_response = client.post(
        f"/api/projects/{project_id}/sources/openapi",
        data={"name": "Commerce OpenAPI"},
        files={
            "file": (
                "commerce.yaml",
                b"""openapi: 3.1.0
info:
  title: Commerce API
  version: 1.0.0
paths:
  /orders:
    post:
      operationId: createOrder
      summary: Create order
      responses:
        '201':
          description: Created
components:
  schemas:
    Order:
      type: object
      properties:
        id:
          type: string
""",
                "application/yaml",
            )
        },
    )
    assert source_response.status_code == 201
    source_id = str(source_response.json()["id"])

    sync_response = client.post(f"/api/sources/{source_id}/synchronizations")
    assert sync_response.status_code == 201
    assert sync_response.json()["status"] == "COMPLETED"
    assert sync_response.json()["operation_count"] == 1
    assert sync_response.json()["schema_count"] == 1

    catalog_response = client.get(
        f"/api/projects/{project_id}/api-catalog",
        params={"source_id": source_id},
    )
    assert catalog_response.status_code == 200
    payload = catalog_response.json()
    assert payload["operation_total"] == 1
    assert payload["schema_total"] == 1
    assert payload["operations"][0]["method"] == "POST"
    assert payload["operations"][0]["path"] == "/orders"
    assert payload["operations"][0]["source_pointer"] == "#/paths/~1orders/post"
    assert payload["schemas"][0]["name"] == "Order"

    runs_response = client.get(f"/api/sources/{source_id}/synchronizations")
    assert runs_response.status_code == 200
    assert runs_response.json()["total"] == 1
