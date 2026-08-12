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
    evidence = make_catalog_evidence(client, project_id)
    create_claim(
        client,
        project_id,
        statement="The Commerce API is part of the implementation contract.",
        classification="OBSERVED",
        evidence_ids=[str(evidence["id"])],
        document_type="LLD",
    )
    return evidence


def make_source_evidence(client: TestClient, project_id: str) -> dict[str, object]:
    source = import_source(client, project_id)
    response = client.post(f"/api/projects/{project_id}/evidence/source-artifacts/{source['id']}")
    assert response.status_code == 201
    return response.json()


def make_catalog_evidence(client: TestClient, project_id: str) -> dict[str, object]:
    source = import_source(client, project_id)
    source_id = str(source["id"])
    synchronization = client.post(f"/api/sources/{source_id}/synchronizations")
    assert synchronization.status_code == 201
    synchronization_id = synchronization.json()["id"]

    evidence_response = client.post(
        f"/api/projects/{project_id}/evidence/catalog-snapshots/{synchronization_id}"
    )
    assert evidence_response.status_code == 201
    return evidence_response.json()


def create_claim(
    client: TestClient,
    project_id: str,
    *,
    statement: str,
    classification: str,
    evidence_ids: list[str],
    document_type: str,
    derivation_reference: str = "",
) -> dict[str, object]:
    payload: dict[str, object] = {
        "statement": statement,
        "classification": classification,
        "evidence_ids": evidence_ids,
        "relevant_document_types": [document_type],
    }
    if derivation_reference:
        payload["derivation_reference"] = derivation_reference

    response = client.post(
        f"/api/projects/{project_id}/claims",
        json=payload,
    )
    assert response.status_code == 201
    return response.json()


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
    assert payload["policyVersion"] == "document-readiness-v3"
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


def test_as_built_generation_rejects_inferred_claim_as_observed_substitute(
    tmp_path: Path,
) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    evidence = make_catalog_evidence(client, project_id)
    inferred = create_claim(
        client,
        project_id,
        statement="The deployment model is inferred from the API boundary.",
        classification="INFERRED",
        evidence_ids=[str(evidence["id"])],
        document_type="AS_BUILT",
        derivation_reference="rule:api-boundary-inference-v1",
    )

    response = client.post(
        f"/api/projects/{project_id}/documents/AS_BUILT/generate",
        json={"revision_reason": "Inference must not satisfy As-Built readiness."},
    )

    assert response.status_code == 409
    payload = response.json()["error"]
    assert payload["code"] == "ENTERPRISE_DOCUMENT_GENERATION_BLOCKED"
    assert payload["documentType"] == "AS_BUILT"
    assert payload["readinessState"] == "NOT_READY"
    finding = next(
        item
        for item in payload["details"]
        if item["rule_code"] == "ASBUILT_OBSERVED_CLAIM_REQUIRED"
    )
    assert finding["severity"] == "BLOCKER"
    assert f"claim:{inferred['id']}:INFERRED" in finding["supporting_references"]

    listed = client.get(f"/api/projects/{project_id}/documents")
    assert listed.status_code == 200
    assert all(item["document_type"] != "AS_BUILT" for item in listed.json()["items"])


def test_as_built_generation_renders_observed_facts_and_reuses_lifecycle(
    tmp_path: Path,
) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    evidence = make_catalog_evidence(client, project_id)

    observed = create_claim(
        client,
        project_id,
        statement="The Commerce API is implemented with the documented orders endpoint.",
        classification="OBSERVED",
        evidence_ids=[str(evidence["id"])],
        document_type="AS_BUILT",
    )
    inferred = create_claim(
        client,
        project_id,
        statement="The deployment model is probably blue-green.",
        classification="INFERRED",
        evidence_ids=[str(evidence["id"])],
        document_type="AS_BUILT",
        derivation_reference="rule:deployment-guess-v1",
    )
    unverified = create_claim(
        client,
        project_id,
        statement="The runtime database is PostgreSQL.",
        classification="UNVERIFIED",
        evidence_ids=[],
        document_type="AS_BUILT",
    )

    response = client.post(
        f"/api/projects/{project_id}/documents/AS_BUILT/generate",
        json={"revision_reason": "Initial governed As-Built draft."},
    )

    assert response.status_code == 201
    document = response.json()
    assert document["document_type"] == "AS_BUILT"
    assert document["version"] == "1.0"
    assert document["status"] == "DRAFT"
    assert "# As-Built Documentation: Generation Foundation" in document["content"]
    assert observed["id"] in document["content"]
    assert (
        "The Commerce API is implemented with the documented orders endpoint."
        in document["content"]
    )
    assert "The deployment model is probably blue-green." not in document["content"]
    assert "The runtime database is PostgreSQL." not in document["content"]
    assert inferred["id"] in document["content"]
    assert unverified["id"] in document["content"]
    assert evidence["id"] in document["content"]

    duplicate_response = client.post(
        f"/api/projects/{project_id}/documents/AS_BUILT/generate",
        json={"revision_reason": "Identical canonical inputs."},
    )
    assert duplicate_response.status_code == 201
    duplicate = duplicate_response.json()
    assert duplicate["id"] == document["id"]
    assert duplicate["reused_existing_version"] is True

    downloaded = client.get(f"/api/documents/{document['id']}/download")
    assert downloaded.status_code == 200
    assert downloaded.headers["x-document-checksum"] == document["checksum"]
    assert downloaded.text == document["content"]


def test_hld_generation_accepts_source_artifact_without_catalog_snapshot(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    evidence = make_source_evidence(client, project_id)

    readiness = client.get(f"/api/projects/{project_id}/readiness/HLD")
    assert readiness.status_code == 200
    assert readiness.json()["readiness_state"] == "PARTIALLY_READY"
    assert readiness.json()["eligible"] is True

    response = client.post(
        f"/api/projects/{project_id}/documents/HLD/generate",
        json={"revision_reason": "Initial source-backed HLD."},
    )

    assert response.status_code == 201
    document = response.json()
    assert document["document_type"] == "HLD"
    assert document["target_run_id"] is None
    assert document["operation_count"] == 0
    assert document["schema_count"] == 0
    assert "# High Level Design: Generation Foundation" in document["content"]
    assert "Primary evidence kind | `SOURCE_ARTIFACT`" in document["content"]
    assert str(evidence["id"]) in document["content"]
    assert "HLD_GOVERNED_CONTEXT_REQUIRED" in document["content"]
    assert "does not invent a synchronization or implementation detail" in document["content"]

    duplicate_response = client.post(
        f"/api/projects/{project_id}/documents/HLD/generate",
        json={"revision_reason": "Identical source-backed inputs."},
    )
    assert duplicate_response.status_code == 201
    duplicate = duplicate_response.json()
    assert duplicate["id"] == document["id"]
    assert duplicate["reused_existing_version"] is True


def test_hld_generation_uses_catalog_snapshot_when_selected_as_evidence(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    evidence = make_catalog_evidence(client, project_id)

    response = client.post(
        f"/api/projects/{project_id}/documents/HLD/generate",
        json={"revision_reason": "Initial catalog-backed HLD."},
    )

    assert response.status_code == 201
    document = response.json()
    assert document["document_type"] == "HLD"
    assert document["target_run_id"] is not None
    assert document["operation_count"] == 1
    assert document["schema_count"] == 1
    assert "Primary evidence kind | `CATALOG_SNAPSHOT`" in document["content"]
    assert str(evidence["id"]) in document["content"]
    assert "### Normalized API boundary" in document["content"]
    assert "`/orders`" in document["content"]


def test_hld_generation_renders_governed_inferred_architecture_context(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    evidence = make_source_evidence(client, project_id)
    inferred = create_claim(
        client,
        project_id,
        statement="The API boundary suggests a commerce-facing service capability.",
        classification="INFERRED",
        evidence_ids=[str(evidence["id"])],
        document_type="HLD",
        derivation_reference="rule:api-boundary-capability-v1",
    )

    readiness = client.get(f"/api/projects/{project_id}/readiness/HLD")
    assert readiness.status_code == 200
    assert readiness.json()["readiness_state"] == "READY"
    assert readiness.json()["eligible"] is True

    response = client.post(
        f"/api/projects/{project_id}/documents/HLD/generate",
        json={"revision_reason": "Add governed architecture context."},
    )

    assert response.status_code == 201
    content = response.json()["content"]
    assert str(inferred["id"]) in content
    expected_inferred = " ".join(
        (
            "**Inferred** — The API boundary suggests a commerce-facing service",
            "capability.",
        )
    )
    assert expected_inferred in content
    assert "rule:api-boundary-capability-v1" in content


def test_hld_generation_remains_blocked_without_any_governed_evidence(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])

    response = client.post(
        f"/api/projects/{project_id}/documents/HLD/generate",
        json={"revision_reason": "No evidence should remain blocked."},
    )

    assert response.status_code == 409
    payload = response.json()["error"]
    assert payload["documentType"] == "HLD"
    assert payload["readinessState"] == "NOT_READY"
    assert payload["policyVersion"] == "document-readiness-v3"
    assert any(
        item["rule_code"] == "HLD_TECHNICAL_EVIDENCE_REQUIRED" for item in payload["details"]
    )
