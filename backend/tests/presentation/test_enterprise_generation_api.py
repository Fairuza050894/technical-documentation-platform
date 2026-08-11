from pathlib import Path

from fastapi.testclient import TestClient

from tdp.config import Settings
from tdp.main import create_app


def build_client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                database_path=tmp_path / "enterprise-generation.sqlite3",
                artifact_root_path=tmp_path / "artifacts",
            )
        )
    )


def create_project(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/projects",
        json={
            "key": "GEN",
            "name": "Generation Foundation",
            "description": "Deterministic enterprise generation.",
            "workspace_type": "PERSONAL",
        },
    )
    assert response.status_code == 201
    return response.json()


def import_source(client: TestClient, project_id: str) -> dict[str, object]:
    response = client.post(
        f"/api/projects/{project_id}/sources/openapi",
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
    get:
      operationId: listOrders
      summary: List orders
      responses:
        '200':
          description: OK
components:
  schemas:
    Order:
      type: object
      required:
        - id
      properties:
        id:
          type: string
""",
                "application/yaml",
            )
        },
    )
    assert response.status_code == 201
    return response.json()


def make_lld_ready(client: TestClient, project_id: str) -> dict[str, object]:
    source = import_source(client, project_id)
    source_id = str(source["id"])
    synchronization = client.post(f"/api/sources/{source_id}/synchronizations")
    assert synchronization.status_code == 201
    synchronization_id = synchronization.json()["id"]

    evidence_response = client.post(
        f"/api/projects/{project_id}/evidence/catalog-snapshots/{synchronization_id}"
    )
    assert evidence_response.status_code == 201
    evidence = evidence_response.json()

    claim = client.post(
        f"/api/projects/{project_id}/claims",
        json={
            "statement": "The Commerce API is part of the implementation contract.",
            "classification": "OBSERVED",
            "evidence_ids": [evidence["id"]],
            "relevant_document_types": ["LLD"],
        },
    )
    assert claim.status_code == 201
    return evidence


def test_generation_is_blocked_with_canonical_readiness_details(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])

    response = client.post(
        f"/api/projects/{project_id}/documents/LLD/generate",
        json={"revision_reason": "Attempt before evidence."},
    )

    assert response.status_code == 409
    payload = response.json()["error"]
    assert payload["code"] == "ENTERPRISE_DOCUMENT_GENERATION_BLOCKED"
    assert payload["documentType"] == "LLD"
    assert payload["readinessState"] == "NOT_READY"
    assert payload["policyVersion"] == "document-readiness-v1"
    assert payload["details"][0]["rule_code"] == "LLD_NORMALIZED_TECHNICAL_EVIDENCE_REQUIRED"


def test_lld_generation_reuses_existing_document_lifecycle_and_download(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    evidence = make_lld_ready(client, project_id)

    response = client.post(
        f"/api/projects/{project_id}/documents/LLD/generate",
        json={"revision_reason": "Initial governed LLD."},
    )
    assert response.status_code == 201
    document = response.json()
    assert document["document_type"] == "LLD"
    assert document["version"] == "1.0"
    assert document["status"] == "DRAFT"
    assert document["reused_existing_version"] is False
    assert "# Low Level Design: Generation Foundation" in document["content"]
    assert evidence["id"] in document["content"]
    assert "The Commerce API is part of the implementation contract." in document["content"]

    duplicate_response = client.post(
        f"/api/projects/{project_id}/documents/LLD/generate",
        json={"revision_reason": "Same canonical inputs."},
    )
    assert duplicate_response.status_code == 201
    duplicate = duplicate_response.json()
    assert duplicate["id"] == document["id"]
    assert duplicate["reused_existing_version"] is True

    listed = client.get(f"/api/projects/{project_id}/documents")
    assert listed.status_code == 200
    assert any(item["document_type"] == "LLD" for item in listed.json()["items"])

    downloaded = client.get(f"/api/documents/{document['id']}/download")
    assert downloaded.status_code == 200
    assert downloaded.headers["x-document-checksum"] == document["checksum"]
    assert downloaded.text == document["content"]


def test_archived_project_blocks_enterprise_generation(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    make_lld_ready(client, project_id)

    archive = client.post(f"/api/projects/{project_id}/archive")
    assert archive.status_code == 200

    response = client.post(
        f"/api/projects/{project_id}/documents/LLD/generate",
        json={"revision_reason": "Must remain blocked."},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DOCUMENT_PROJECT_ARCHIVED"
