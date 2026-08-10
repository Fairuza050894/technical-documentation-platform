from pathlib import Path

from fastapi.testclient import TestClient

from tdp.config import Settings
from tdp.main import create_app


def build_client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                database_path=tmp_path / "evidence.sqlite3",
                artifact_root_path=tmp_path / "artifacts",
            )
        )
    )


def create_project(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/projects",
        json={
            "key": "EVIDENCE",
            "name": "Evidence Foundation",
            "description": "Traceable evidence and claims.",
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
      responses:
        '200':
          description: OK
""",
                "application/yaml",
            )
        },
    )
    assert response.status_code == 201
    return response.json()


def test_source_and_snapshot_become_checksum_backed_evidence(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    source = import_source(client, project_id)
    source_id = str(source["id"])

    source_evidence_response = client.post(
        f"/api/projects/{project_id}/evidence/source-artifacts/{source_id}"
    )
    assert source_evidence_response.status_code == 201
    source_evidence = source_evidence_response.json()
    assert source_evidence["kind"] == "SOURCE_ARTIFACT"
    assert source_evidence["checksum"] == source["checksum"]
    assert source_evidence["content_reference"] == f"source-artifact:{source_id}"

    synchronization_response = client.post(f"/api/sources/{source_id}/synchronizations")
    assert synchronization_response.status_code == 201
    synchronization = synchronization_response.json()

    snapshot_response = client.post(
        f"/api/projects/{project_id}/evidence/catalog-snapshots/{synchronization['id']}"
    )
    assert snapshot_response.status_code == 201
    snapshot = snapshot_response.json()
    assert snapshot["kind"] == "CATALOG_SNAPSHOT"
    assert len(snapshot["checksum"]) == 64
    assert snapshot["checksum"] != ""

    repeated = client.post(
        f"/api/projects/{project_id}/evidence/catalog-snapshots/{synchronization['id']}"
    )
    assert repeated.status_code == 201
    assert repeated.json()["id"] == snapshot["id"]

    collection = client.get(f"/api/projects/{project_id}/evidence").json()
    assert collection["total"] == 2


def test_claim_classification_and_document_relevance_are_governed(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    source = import_source(client, project_id)

    evidence = client.post(
        f"/api/projects/{project_id}/evidence/source-artifacts/{source['id']}"
    ).json()

    observed_response = client.post(
        f"/api/projects/{project_id}/claims",
        json={
            "statement": "The project exposes a Commerce OpenAPI source.",
            "classification": "OBSERVED",
            "evidence_ids": [evidence["id"]],
            "relevant_document_types": ["HLD", "LLD", "AS_BUILT"],
        },
    )
    assert observed_response.status_code == 201
    observed = observed_response.json()
    assert observed["classification"] == "OBSERVED"
    assert observed["evidence_ids"] == [evidence["id"]]
    assert observed["relevant_document_types"] == ["HLD", "LLD", "AS_BUILT"]

    inferred_response = client.post(
        f"/api/projects/{project_id}/claims",
        json={
            "statement": "The Commerce API forms part of the implementation boundary.",
            "classification": "INFERRED",
            "evidence_ids": [evidence["id"]],
            "derivation_reference": "rule:source-boundary-v1",
            "relevant_document_types": ["HLD"],
        },
    )
    assert inferred_response.status_code == 201
    assert inferred_response.json()["classification"] == "INFERRED"

    invalid_observed = client.post(
        f"/api/projects/{project_id}/claims",
        json={
            "statement": "Unsupported factual assertion.",
            "classification": "OBSERVED",
            "evidence_ids": [],
        },
    )
    assert invalid_observed.status_code == 422
    assert invalid_observed.json()["error"]["code"] == "INVALID_CLAIM_EVIDENCE"

    invalid_document_type = client.post(
        f"/api/projects/{project_id}/claims",
        json={
            "statement": "Potential deployment note.",
            "classification": "UNVERIFIED",
            "relevant_document_types": ["TECHNICAL_SOURCE_OVERVIEW"],
        },
    )
    assert invalid_document_type.status_code == 422
    assert invalid_document_type.json()["error"]["code"] == "INVALID_CLAIM_DOCUMENT_TYPE"


def test_archived_project_keeps_evidence_and_claims_readable_but_blocks_mutation(
    tmp_path: Path,
) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    source = import_source(client, project_id)
    evidence = client.post(
        f"/api/projects/{project_id}/evidence/source-artifacts/{source['id']}"
    ).json()
    claim = client.post(
        f"/api/projects/{project_id}/claims",
        json={
            "statement": "The imported source is preserved as evidence.",
            "classification": "OBSERVED",
            "evidence_ids": [evidence["id"]],
            "relevant_document_types": ["AS_BUILT"],
        },
    ).json()

    assert client.post(f"/api/projects/{project_id}/archive").status_code == 200

    evidence_read = client.get(f"/api/projects/{project_id}/evidence")
    claims_read = client.get(f"/api/projects/{project_id}/claims")
    assert evidence_read.status_code == 200
    assert evidence_read.json()["total"] == 1
    assert claims_read.status_code == 200
    assert claims_read.json()["items"][0]["id"] == claim["id"]

    blocked_claim = client.post(
        f"/api/projects/{project_id}/claims",
        json={
            "statement": "A new claim after archive.",
            "classification": "UNVERIFIED",
        },
    )
    assert blocked_claim.status_code == 409
    assert blocked_claim.json()["error"]["code"] == "EVIDENCE_PROJECT_ARCHIVED"

    blocked_evidence = client.post(
        f"/api/projects/{project_id}/evidence/source-artifacts/{source['id']}"
    )
    assert blocked_evidence.status_code == 409
    assert blocked_evidence.json()["error"]["code"] == "EVIDENCE_PROJECT_ARCHIVED"
