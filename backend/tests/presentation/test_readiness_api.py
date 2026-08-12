from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from tdp.config import Settings
from tdp.main import create_app


def build_client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                database_path=tmp_path / "readiness.sqlite3",
                artifact_root_path=tmp_path / "artifacts",
            )
        )
    )


def create_project(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/projects",
        json={
            "key": "READY",
            "name": "Readiness Foundation",
            "description": "Deterministic document readiness.",
            "workspace_type": "PERSONAL",
        },
    )
    assert response.status_code == 201
    return response.json()


def import_source(client: TestClient, project_id: str) -> dict[str, object]:
    response = client.post(
        f"/api/projects/{project_id}/sources/openapi",
        data={"name": "Readiness API"},
        files={
            "file": (
                "readiness.yaml",
                b"""openapi: 3.1.0
info:
  title: Readiness API
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


def register_referenced_evidence(
    client: TestClient,
    project_id: str,
    *,
    kind: str,
    origin_id: str,
    checksum_character: str,
) -> dict[str, object]:
    response = client.post(
        f"/api/projects/{project_id}/evidence/references",
        json={
            "kind": kind,
            "source_reference": f"governed-source:{origin_id}",
            "origin_id": origin_id,
            "checksum": checksum_character * 64,
            "content_reference": f"evidence-manifest:{origin_id}",
            "captured_at": "2026-08-12T02:00:00+00:00",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_empty_project_exposes_explainable_not_ready_profiles(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])

    response = client.get(f"/api/projects/{project_id}/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["policy_version"] == "document-readiness-v2"
    assert payload["total"] == 10
    assert payload["required_total"] == 7
    assert payload["not_ready_total"] == 10
    assert payload["eligible_total"] == 0

    hld = next(item for item in payload["items"] if item["document_type"] == "HLD")
    assert hld["availability"] == "MISSING"
    assert hld["readiness_state"] == "NOT_READY"
    assert hld["eligible"] is False
    assert hld["findings"][0]["rule_code"] == "HLD_TECHNICAL_EVIDENCE_REQUIRED"


def test_current_evidence_can_make_hld_lld_and_as_built_ready(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    source = import_source(client, project_id)
    source_id = str(source["id"])

    source_evidence = client.post(
        f"/api/projects/{project_id}/evidence/source-artifacts/{source_id}"
    )
    assert source_evidence.status_code == 201

    sync_response = client.post(f"/api/sources/{source_id}/synchronizations")
    assert sync_response.status_code == 201
    synchronization_id = sync_response.json()["id"]

    snapshot_response = client.post(
        f"/api/projects/{project_id}/evidence/catalog-snapshots/{synchronization_id}"
    )
    assert snapshot_response.status_code == 201
    snapshot = snapshot_response.json()

    claim_response = client.post(
        f"/api/projects/{project_id}/claims",
        json={
            "statement": "The normalized Commerce boundary is present in implementation evidence.",
            "classification": "OBSERVED",
            "evidence_ids": [snapshot["id"]],
            "relevant_document_types": ["HLD", "LLD", "AS_BUILT"],
        },
    )
    assert claim_response.status_code == 201

    response = client.get(f"/api/projects/{project_id}/readiness")
    assert response.status_code == 200
    payload = response.json()
    by_type = {item["document_type"]: item for item in payload["items"]}

    assert by_type["HLD"]["readiness_state"] == "READY"
    assert by_type["LLD"]["readiness_state"] == "READY"
    assert by_type["AS_BUILT"]["readiness_state"] == "READY"
    assert by_type["DEVELOPER_ONBOARDING_BRIEF"]["readiness_state"] == "PARTIALLY_READY"
    assert by_type["USER_GUIDE"]["readiness_state"] == "NOT_READY"
    assert payload["ready_total"] == 3
    assert payload["partially_ready_total"] == 1
    assert payload["eligible_total"] == 4


def test_readiness_remains_readable_for_archived_project(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])

    before = client.get(f"/api/projects/{project_id}/readiness")
    assert before.status_code == 200

    archive = client.post(f"/api/projects/{project_id}/archive")
    assert archive.status_code == 200

    after = client.get(f"/api/projects/{project_id}/readiness")
    assert after.status_code == 200
    assert after.json()["project_status"] == "ARCHIVED"
    assert after.json()["items"] == before.json()["items"]


def test_document_readiness_rejects_unknown_document_type(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)

    response = client.get(f"/api/projects/{project['id']}/readiness/TECHNICAL_SOURCE_OVERVIEW")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_READINESS_DOCUMENT_TYPE"


def test_readiness_rejects_unknown_project(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get(f"/api/projects/{uuid4()}/readiness")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "READINESS_PROJECT_NOT_FOUND"


def test_semantic_evidence_unlocks_matching_profiles_without_unlocking_hld(
    tmp_path: Path,
) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])

    register_referenced_evidence(
        client,
        project_id,
        kind="USER_JOURNEY",
        origin_id="journey-v1",
        checksum_character="a",
    )
    register_referenced_evidence(
        client,
        project_id,
        kind="DEPLOYMENT_RUNTIME",
        origin_id="deployment-v1",
        checksum_character="b",
    )
    register_referenced_evidence(
        client,
        project_id,
        kind="UAT_RESULT",
        origin_id="uat-v1",
        checksum_character="c",
    )

    response = client.get(f"/api/projects/{project_id}/readiness")
    assert response.status_code == 200
    payload = response.json()
    assert payload["policy_version"] == "document-readiness-v2"
    by_type = {item["document_type"]: item for item in payload["items"]}

    assert by_type["HLD"]["readiness_state"] == "NOT_READY"
    assert by_type["DEVELOPER_ONBOARDING_BRIEF"]["readiness_state"] == "NOT_READY"
    assert by_type["USER_GUIDE"]["readiness_state"] == "PARTIALLY_READY"
    assert by_type["USER_GUIDE"]["eligible"] is True
    assert by_type["JOURNEY_MAP"]["readiness_state"] == "READY"
    assert by_type["INSTALLATION_GUIDE"]["readiness_state"] == "READY"
    assert by_type["UAT_EVIDENCE"]["readiness_state"] == "READY"
    assert payload["eligible_total"] == 4
