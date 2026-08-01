from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from tdp.config import Settings
from tdp.main import create_app


def build_client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                database_path=tmp_path / "document-lifecycle.sqlite3",
                artifact_root_path=tmp_path / "artifacts",
            )
        )
    )


def create_project(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/api/projects",
        json={
            "key": "DOCS",
            "name": "Documentation Platform",
            "description": "Commerce documentation.",
            "workspace_type": "PERSONAL",
        },
    )
    assert response.status_code == 201
    return response.json()


def synchronize_source(
    client: TestClient,
    project_id: str,
    *,
    source_name: str,
    api_version: str,
    include_validation_endpoint: bool,
) -> dict[str, Any]:
    extra_path = (
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
      summary: Create an order
      responses:
        '201':
          description: Created
{extra_path}components:
  schemas:
    Order:
      type: object
      required: [id]
      properties:
        id:
          type: string
          format: uuid
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
    return synchronization_response.json()


def generate(
    client: TestClient,
    project_id: str,
    target_run_id: str,
    *,
    revision_reason: str,
) -> dict[str, Any]:
    response = client.post(
        f"/api/projects/{project_id}/documents/technical-source-overview",
        json={
            "target_run_id": target_run_id,
            "baseline_run_id": None,
            "revision_reason": revision_reason,
        },
    )
    assert response.status_code == 201
    return response.json()


def workflow_action(
    client: TestClient,
    version_id: str,
    action: str,
    *,
    comment: str = "",
) -> dict[str, Any]:
    response = client.post(
        f"/api/document-versions/{version_id}/{action}",
        json={"comment": comment},
    )
    assert response.status_code == 200
    return response.json()


def test_generation_reuses_identical_content_without_duplicate_version(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    run = synchronize_source(
        client,
        project["id"],
        source_name="Commerce API v1",
        api_version="1.0.0",
        include_validation_endpoint=False,
    )

    first = generate(
        client,
        project["id"],
        run["id"],
        revision_reason="Initial deterministic overview.",
    )
    duplicate = generate(
        client,
        project["id"],
        run["id"],
        revision_reason="This reason must not create duplicate content.",
    )

    assert first["version"] == "1.0"
    assert first["status"] == "DRAFT"
    assert first["created_by"] == "Technical Writer [local:local-technical-writer]"
    assert first["reused_existing_version"] is False
    assert duplicate["id"] == first["id"]
    assert duplicate["document_id"] == first["document_id"]
    assert duplicate["reused_existing_version"] is True

    versions_response = client.get(f"/api/documents/{first['document_id']}/versions")
    assert versions_response.status_code == 200
    assert versions_response.json()["total"] == 1


def test_review_approval_and_automatic_supersede_are_audited(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    first_run = synchronize_source(
        client,
        project["id"],
        source_name="Commerce API v1",
        api_version="1.0.0",
        include_validation_endpoint=False,
    )
    second_run = synchronize_source(
        client,
        project["id"],
        source_name="Commerce API v2",
        api_version="2.0.0",
        include_validation_endpoint=True,
    )

    first = generate(
        client,
        project["id"],
        first_run["id"],
        revision_reason="Initial approved baseline.",
    )
    workflow_action(client, first["id"], "submit-review")
    first_approved = workflow_action(
        client,
        first["id"],
        "approve",
        comment="Approved against OpenAPI v1.",
    )
    assert first_approved["status"] == "APPROVED"

    second = generate(
        client,
        project["id"],
        second_run["id"],
        revision_reason="Add order validation endpoint.",
    )
    assert second["document_id"] == first["document_id"]
    assert second["version"] == "1.1"
    workflow_action(client, second["id"], "submit-review")
    second_approved = workflow_action(
        client,
        second["id"],
        "approve",
        comment="Approved against OpenAPI v2.",
    )
    assert second_approved["status"] == "APPROVED"

    first_detail = client.get(f"/api/document-versions/{first['id']}")
    assert first_detail.status_code == 200
    assert first_detail.json()["status"] == "SUPERSEDED"

    second_events = client.get(f"/api/document-versions/{second['id']}/workflow-events")
    assert second_events.status_code == 200
    assert [item["action"] for item in second_events.json()["items"]] == [
        "GENERATED",
        "SUBMITTED_FOR_REVIEW",
        "APPROVED",
    ]
    assert {item["actor"] for item in second_events.json()["items"]} == {
        "Technical Writer [local:local-technical-writer]"
    }

    first_events = client.get(f"/api/document-versions/{first['id']}/workflow-events")
    assert first_events.status_code == 200
    assert first_events.json()["items"][-1]["action"] == "SUPERSEDED"


def test_invalid_workflow_transition_returns_conflict(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    run = synchronize_source(
        client,
        project["id"],
        source_name="Commerce API",
        api_version="1.0.0",
        include_validation_endpoint=False,
    )
    version = generate(
        client,
        project["id"],
        run["id"],
        revision_reason="Initial draft.",
    )

    response = client.post(
        f"/api/document-versions/{version['id']}/approve",
        json={"comment": "Premature approval."},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_DOCUMENT_WORKFLOW_TRANSITION"


def test_workflow_rejects_client_supplied_actor(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.post(
        "/api/document-versions/00000000-0000-4000-8000-000000000001/approve",
        json={"actor": "Spoofed Approver", "comment": "This identity must not be accepted."},
    )

    assert response.status_code == 422
    fields = {item["field"] for item in response.json()["error"]["details"]}
    assert "actor" in fields


def test_generation_rejects_client_supplied_actor(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.post(
        "/api/projects/project-id/documents/technical-source-overview",
        json={
            "target_run_id": "synchronization-id",
            "baseline_run_id": None,
            "revision_reason": "Attempt to spoof identity.",
            "actor": "Spoofed Generator",
        },
    )

    assert response.status_code == 422
    fields = {item["field"] for item in response.json()["error"]["details"]}
    assert "actor" in fields
