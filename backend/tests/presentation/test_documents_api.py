from pathlib import Path

from fastapi.testclient import TestClient

from tdp.config import Settings
from tdp.main import create_app


def build_client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                database_path=tmp_path / "documents.sqlite3",
                artifact_root_path=tmp_path / "artifacts",
            )
        )
    )


def test_generate_list_get_and_download_technical_source_overview(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project_response = client.post(
        "/api/projects",
        json={
            "key": "DOCS",
            "name": "Documentation Platform",
            "description": "Commerce documentation.",
            "workspace_type": "PERSONAL",
        },
    )
    assert project_response.status_code == 201
    project = project_response.json()

    source_response = client.post(
        f"/api/projects/{project['id']}/sources/openapi",
        data={"name": "Commerce API"},
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
      summary: Create an order
      tags: [Orders]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateOrderRequest'
      responses:
        '201':
          description: Created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
components:
  schemas:
    CreateOrderRequest:
      type: object
      required: [customerId]
      properties:
        customerId:
          type: string
          format: uuid
    Order:
      type: object
      required: [id]
      properties:
        id:
          type: string
          format: uuid
""",
                "application/yaml",
            )
        },
    )
    assert source_response.status_code == 201
    source = source_response.json()

    synchronization_response = client.post(
        f"/api/sources/{source['id']}/synchronizations"
    )
    assert synchronization_response.status_code == 201
    synchronization = synchronization_response.json()

    generation_response = client.post(
        f"/api/projects/{project['id']}/documents/technical-source-overview",
        json={
            "target_run_id": synchronization["id"],
            "baseline_run_id": None,
        },
    )
    assert generation_response.status_code == 201
    document = generation_response.json()
    assert document["document_type"] == "TECHNICAL_SOURCE_OVERVIEW"
    assert document["document_format"] == "MARKDOWN"
    assert len(document["checksum"]) == 64
    assert "# Technical Source Overview: Commerce API" in document["content"]
    assert "#/paths/~1orders/post" in document["content"]

    collection_response = client.get(f"/api/projects/{project['id']}/documents")
    assert collection_response.status_code == 200
    assert collection_response.json()["total"] == 1

    detail_response = client.get(f"/api/documents/{document['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["checksum"] == document["checksum"]

    download_response = client.get(f"/api/documents/{document['id']}/download")
    assert download_response.status_code == 200
    assert download_response.headers["content-type"].startswith("text/markdown")
    assert document["file_name"] in download_response.headers["content-disposition"]
    assert download_response.headers["x-document-checksum"] == document["checksum"]
    assert download_response.text == document["content"]
