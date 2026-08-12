from pathlib import Path

from fastapi.testclient import TestClient

from tdp.config import Settings
from tdp.main import create_app
from tdp.modules.evidence.domain.materialization import (
    canonicalize_semantic_evidence_manifest,
)
from tdp.modules.evidence.domain.model import EvidenceKind


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


def referenced_evidence_payload(
    kind: str,
    *,
    origin_id: str,
    checksum_character: str,
) -> dict[str, object]:
    return {
        "kind": kind,
        "source_reference": f"governed-source:{origin_id}",
        "origin_id": origin_id,
        "checksum": checksum_character * 64,
        "content_reference": f"evidence-manifest:{origin_id}",
        "captured_at": "2026-08-12T02:00:00+00:00",
    }


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


def test_referenced_semantic_evidence_registration_is_governed_and_idempotent(
    tmp_path: Path,
) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])

    created: list[dict[str, object]] = []
    for kind, origin_id, checksum_character in (
        ("USER_JOURNEY", "journey-checkout-v1", "a"),
        ("DEPLOYMENT_RUNTIME", "deployment-release-v1", "b"),
        ("UAT_RESULT", "uat-release-v1", "c"),
    ):
        payload = referenced_evidence_payload(
            kind,
            origin_id=origin_id,
            checksum_character=checksum_character,
        )
        response = client.post(
            f"/api/projects/{project_id}/evidence/references",
            json=payload,
        )
        assert response.status_code == 201
        artifact = response.json()
        assert artifact["kind"] == kind
        assert artifact["source_system"] == "GOVERNED_REFERENCE"
        assert artifact["collection_method"] == "REFERENCE_REGISTRATION"
        created.append(artifact)

        repeated = client.post(
            f"/api/projects/{project_id}/evidence/references",
            json=payload,
        )
        assert repeated.status_code == 201
        assert repeated.json()["id"] == artifact["id"]

    collection = client.get(f"/api/projects/{project_id}/evidence")
    assert collection.status_code == 200
    assert collection.json()["total"] == 3
    assert {item["id"] for item in collection.json()["items"]} == {
        str(item["id"]) for item in created
    }


def test_referenced_evidence_rejects_conflicting_origin_and_metadata_spoofing(
    tmp_path: Path,
) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    payload = referenced_evidence_payload(
        "USER_JOURNEY",
        origin_id="journey-conflict-v1",
        checksum_character="d",
    )

    first = client.post(
        f"/api/projects/{project_id}/evidence/references",
        json=payload,
    )
    assert first.status_code == 201

    conflicting = dict(payload)
    conflicting["checksum"] = "e" * 64
    conflict = client.post(
        f"/api/projects/{project_id}/evidence/references",
        json=conflicting,
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "EVIDENCE_ORIGIN_CONFLICT"

    spoofed = dict(payload)
    spoofed["source_system"] = "API_CATALOG"
    spoofed["collection_method"] = "DETERMINISTIC_NORMALIZATION"
    spoof = client.post(
        f"/api/projects/{project_id}/evidence/references",
        json=spoofed,
    )
    assert spoof.status_code == 422

    unsupported = referenced_evidence_payload(
        "SOURCE_ARTIFACT",
        origin_id="unsupported-source-v1",
        checksum_character="f",
    )
    rejected = client.post(
        f"/api/projects/{project_id}/evidence/references",
        json=unsupported,
    )
    assert rejected.status_code == 422


def test_archived_project_blocks_referenced_semantic_evidence(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    assert client.post(f"/api/projects/{project_id}/archive").status_code == 200

    response = client.post(
        f"/api/projects/{project_id}/evidence/references",
        json=referenced_evidence_payload(
            "UAT_RESULT",
            origin_id="uat-after-archive",
            checksum_character="a",
        ),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EVIDENCE_PROJECT_ARCHIVED"


def deployment_materialization_manifest() -> dict[str, object]:
    return {
        "schema_version": "semantic-evidence-manifest-v1",
        "kind": "DEPLOYMENT_RUNTIME",
        "payload": {
            "environment": "staging",
            "runtime_components": [
                {
                    "name": "api",
                    "version": "1.4.0",
                    "source_reference": "deployment-run:release-42",
                }
            ],
            "prerequisites": ["Container runtime is available."],
            "configuration_keys": ["DATABASE_URL", "LOG_LEVEL"],
            "deployment_steps": [
                {
                    "sequence": 1,
                    "instruction": "Apply the approved deployment bundle.",
                    "source_reference": "pipeline-step:deploy",
                }
            ],
            "verification_checks": [
                {
                    "name": "Readiness endpoint",
                    "expected_result": "The service reports healthy.",
                    "source_reference": "pipeline-step:verify",
                }
            ],
            "rollback_references": ["runbook:rollback-release-42"],
        },
    }


def test_referenced_evidence_materialization_is_checksum_verified_and_idempotent(
    tmp_path: Path,
) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    manifest = deployment_materialization_manifest()
    canonical = canonicalize_semantic_evidence_manifest(
        EvidenceKind.DEPLOYMENT_RUNTIME,
        manifest,
    )
    registered = client.post(
        f"/api/projects/{project_id}/evidence/references",
        json={
            "kind": "DEPLOYMENT_RUNTIME",
            "source_reference": "deployment-run:release-42",
            "origin_id": "release-42",
            "checksum": str(canonical.checksum),
            "content_reference": "evidence-manifest:release-42",
            "captured_at": "2026-08-12T04:00:00+00:00",
        },
    )
    assert registered.status_code == 201
    artifact = registered.json()

    first = client.post(
        f"/api/projects/{project_id}/evidence/{artifact['id']}/materialization",
        json={"manifest": manifest},
    )
    repeated = client.post(
        f"/api/projects/{project_id}/evidence/{artifact['id']}/materialization",
        json={"manifest": manifest},
    )
    fetched = client.get(f"/api/evidence/{artifact['id']}/materialization")

    assert first.status_code == 201
    assert repeated.status_code == 201
    assert fetched.status_code == 200
    assert first.json() == repeated.json() == fetched.json()
    assert first.json()["kind"] == "DEPLOYMENT_RUNTIME"
    assert first.json()["checksum"] == str(canonical.checksum)
    assert "canonical_manifest" not in first.json()


def test_materialization_rejects_checksum_mismatch_and_missing_lookup(
    tmp_path: Path,
) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    registered = client.post(
        f"/api/projects/{project_id}/evidence/references",
        json=referenced_evidence_payload(
            "DEPLOYMENT_RUNTIME",
            origin_id="release-mismatch",
            checksum_character="f",
        ),
    )
    assert registered.status_code == 201
    artifact = registered.json()

    missing = client.get(f"/api/evidence/{artifact['id']}/materialization")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "EVIDENCE_MATERIALIZATION_NOT_FOUND"

    mismatch = client.post(
        f"/api/projects/{project_id}/evidence/{artifact['id']}/materialization",
        json={"manifest": deployment_materialization_manifest()},
    )
    assert mismatch.status_code == 409
    assert mismatch.json()["error"]["code"] == "EVIDENCE_MATERIALIZATION_CHECKSUM_MISMATCH"


def test_archived_project_blocks_new_materialization(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    manifest = deployment_materialization_manifest()
    canonical = canonicalize_semantic_evidence_manifest(
        EvidenceKind.DEPLOYMENT_RUNTIME,
        manifest,
    )
    registered = client.post(
        f"/api/projects/{project_id}/evidence/references",
        json={
            "kind": "DEPLOYMENT_RUNTIME",
            "source_reference": "deployment-run:release-archive",
            "origin_id": "release-archive",
            "checksum": str(canonical.checksum),
            "content_reference": "evidence-manifest:release-archive",
            "captured_at": "2026-08-12T04:00:00+00:00",
        },
    ).json()

    assert client.post(f"/api/projects/{project_id}/archive").status_code == 200
    blocked = client.post(
        f"/api/projects/{project_id}/evidence/{registered['id']}/materialization",
        json={"manifest": manifest},
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "EVIDENCE_PROJECT_ARCHIVED"


def test_materialization_conflict_does_not_replace_history(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    manifest = deployment_materialization_manifest()
    canonical = canonicalize_semantic_evidence_manifest(
        EvidenceKind.DEPLOYMENT_RUNTIME,
        manifest,
    )
    artifact = client.post(
        f"/api/projects/{project_id}/evidence/references",
        json={
            "kind": "DEPLOYMENT_RUNTIME",
            "source_reference": "deployment-run:release-conflict",
            "origin_id": "release-conflict",
            "checksum": str(canonical.checksum),
            "content_reference": "evidence-manifest:release-conflict",
            "captured_at": "2026-08-12T04:00:00+00:00",
        },
    ).json()
    assert (
        client.post(
            f"/api/projects/{project_id}/evidence/{artifact['id']}/materialization",
            json={"manifest": manifest},
        ).status_code
        == 201
    )

    changed = deployment_materialization_manifest()
    changed_payload = changed["payload"]
    assert isinstance(changed_payload, dict)
    changed_payload["environment"] = "production"
    response = client.post(
        f"/api/projects/{project_id}/evidence/{artifact['id']}/materialization",
        json={"manifest": changed},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EVIDENCE_MATERIALIZATION_CONFLICT"


def test_archived_feature_blocks_new_materialization(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    workspace_id = str(project["workspace_id"])
    feature_base_path = f"/api/workspaces/{workspace_id}/projects/{project_id}/features"
    feature = client.post(
        feature_base_path,
        json={
            "key": "CHECKOUT",
            "name": "Checkout",
            "description": "Checkout journey.",
            "kind": "FEATURE",
            "owner": "Documentation Team",
        },
    )
    assert feature.status_code == 201
    feature_id = str(feature.json()["id"])

    manifest = deployment_materialization_manifest()
    canonical = canonicalize_semantic_evidence_manifest(
        EvidenceKind.DEPLOYMENT_RUNTIME,
        manifest,
    )
    artifact = client.post(
        f"/api/projects/{project_id}/evidence/references",
        json={
            "kind": "DEPLOYMENT_RUNTIME",
            "source_reference": "deployment-run:feature-release",
            "origin_id": "feature-release",
            "checksum": str(canonical.checksum),
            "content_reference": "evidence-manifest:feature-release",
            "captured_at": "2026-08-12T04:00:00+00:00",
            "feature_id": feature_id,
        },
    )
    assert artifact.status_code == 201

    archived = client.post(f"{feature_base_path}/{feature_id}/archive")
    assert archived.status_code == 200

    blocked = client.post(
        f"/api/projects/{project_id}/evidence/{artifact.json()['id']}/materialization",
        json={"manifest": manifest},
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "EVIDENCE_FEATURE_ARCHIVED"
