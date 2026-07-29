from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from tdp.config import Settings
from tdp.main import create_app


def build_client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                database_path=tmp_path / "document-version-comparison.sqlite3",
                artifact_root_path=tmp_path / "artifacts",
            )
        )
    )


def create_project(client: TestClient, *, key: str) -> dict[str, Any]:
    response = client.post(
        "/api/projects",
        json={
            "key": key,
            "name": f"{key} Documentation",
            "description": "Deterministic comparison project.",
            "workspace_type": "PERSONAL",
        },
    )
    assert response.status_code == 201
    return response.json()


def generate_version(
    client: TestClient,
    project_id: str,
    *,
    source_name: str,
    api_version: str,
    include_validation_endpoint: bool,
) -> dict[str, Any]:
    validation_path = (
        """
  /orders/validate:
    post:
      operationId: validateOrder
      responses:
        '204':
          description: Valid
"""
        if include_validation_endpoint
        else ""
    )
    content = f"""openapi: 3.1.0
info:
  title: Commerce API
  version: {api_version}
paths:
  /orders:
    post:
      operationId: createOrder
      responses:
        '201':
          description: Created
{validation_path}components:
  schemas:
    Order:
      type: object
      properties:
        id:
          type: string
""".encode()
    source_response = client.post(
        f"/api/projects/{project_id}/sources/openapi",
        data={"name": source_name},
        files={"file": (f"{source_name}.yaml", content, "application/yaml")},
    )
    assert source_response.status_code == 201
    source = source_response.json()

    synchronization_response = client.post(f"/api/sources/{source['id']}/synchronizations")
    assert synchronization_response.status_code == 201
    synchronization = synchronization_response.json()

    generation_response = client.post(
        f"/api/projects/{project_id}/documents/technical-source-overview",
        json={
            "target_run_id": synchronization["id"],
            "baseline_run_id": None,
            "revision_reason": f"Generate API {api_version}.",
            "actor": "Technical Writer",
        },
    )
    assert generation_response.status_code == 201
    return generation_response.json()


def test_compare_document_versions_returns_structured_section_changes(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client, key="DOCS")
    baseline = generate_version(
        client,
        project["id"],
        source_name="Commerce API v1",
        api_version="1.0.0",
        include_validation_endpoint=False,
    )
    target = generate_version(
        client,
        project["id"],
        source_name="Commerce API v2",
        api_version="2.0.0",
        include_validation_endpoint=True,
    )

    response = client.post(
        "/api/document-version-comparisons",
        json={
            "baseline_version_id": baseline["id"],
            "target_version_id": target["id"],
        },
    )

    assert response.status_code == 200
    comparison = response.json()
    assert comparison["document_id"] == baseline["document_id"]
    assert comparison["target_version_id"] == target["id"]
    assert comparison["modified_total"] >= 1
    assert comparison["total"] == len(comparison["changes"])
    assert any(
        change["section_key"] == "endpoint-catalog" and change["kind"] == "MODIFIED"
        for change in comparison["changes"]
    )


def test_compare_document_versions_rejects_different_document_series(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    first_project = create_project(client, key="DOCS")
    second_project = create_project(client, key="PORTAL")
    first = generate_version(
        client,
        first_project["id"],
        source_name="Commerce API",
        api_version="1.0.0",
        include_validation_endpoint=False,
    )
    second = generate_version(
        client,
        second_project["id"],
        source_name="Portal API",
        api_version="1.0.0",
        include_validation_endpoint=False,
    )

    response = client.post(
        "/api/document-version-comparisons",
        json={
            "baseline_version_id": first["id"],
            "target_version_id": second["id"],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_DOCUMENT_VERSION_COMPARISON"
