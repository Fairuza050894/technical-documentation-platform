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
                database_path=tmp_path / "semantic-generation.sqlite3",
                artifact_root_path=tmp_path / "artifacts",
            )
        )
    )


def create_project(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/projects",
        json={
            "key": "SEM",
            "name": "Semantic Generation",
            "description": "Governed semantic document generation.",
            "workspace_type": "PERSONAL",
        },
    )
    assert response.status_code == 201
    return response.json()


def semantic_manifest(kind: str, origin_id: str) -> dict[str, object]:
    if kind == "USER_JOURNEY":
        payload: dict[str, object] = {
            "journey_name": "Checkout",
            "actors": ["Operator"],
            "preconditions": ["The operator is signed in."],
            "steps": [
                {
                    "sequence": 1,
                    "actor": "Operator",
                    "action": "Submit the checkout form.",
                    "expected_outcome": "The order is accepted.",
                    "source_reference": f"journey-step:{origin_id}",
                }
            ],
            "outcomes": ["The order is visible in monitoring."],
        }
    elif kind == "DEPLOYMENT_RUNTIME":
        payload = {
            "environment": "staging",
            "runtime_components": [
                {
                    "name": "api",
                    "version": "1.4.0",
                    "source_reference": f"deployment-run:{origin_id}",
                }
            ],
            "prerequisites": ["Container runtime is available."],
            "configuration_keys": ["DATABASE_URL"],
            "deployment_steps": [
                {
                    "sequence": 1,
                    "instruction": "Apply the approved deployment bundle.",
                    "source_reference": f"pipeline-step:{origin_id}",
                }
            ],
            "verification_checks": [
                {
                    "name": "Readiness",
                    "expected_result": "The service reports healthy.",
                    "source_reference": f"pipeline-check:{origin_id}",
                }
            ],
            "rollback_references": [f"runbook:{origin_id}"],
        }
    else:
        payload = {
            "run_reference": f"uat-run:{origin_id}",
            "executed_at": "2026-08-14T02:00:00+00:00",
            "scenarios": [
                {
                    "scenario_id": "UAT-001",
                    "title": "Checkout succeeds",
                    "status": "PASSED",
                    "expected_result": "The order is created.",
                    "actual_result": "The order was created.",
                    "evidence_references": [f"uat-evidence:{origin_id}"],
                },
                {
                    "scenario_id": "UAT-002",
                    "title": "Invalid checkout is rejected",
                    "status": "BLOCKED",
                    "expected_result": "Validation feedback is returned.",
                    "actual_result": "Environment dependency was unavailable.",
                    "evidence_references": [f"uat-evidence:{origin_id}:2"],
                },
            ],
        }
    return {
        "schema_version": "semantic-evidence-manifest-v1",
        "kind": kind,
        "payload": payload,
    }


def register_semantic_evidence(
    client: TestClient,
    project_id: str,
    *,
    kind: str,
    origin_id: str,
    materialize: bool = True,
) -> dict[str, object]:
    manifest = semantic_manifest(kind, origin_id)
    canonical = canonicalize_semantic_evidence_manifest(EvidenceKind(kind), manifest)
    response = client.post(
        f"/api/projects/{project_id}/evidence/references",
        json={
            "kind": kind,
            "source_reference": f"governed-source:{origin_id}",
            "origin_id": origin_id,
            "checksum": str(canonical.checksum),
            "content_reference": f"evidence-manifest:{origin_id}",
            "captured_at": "2026-08-14T02:00:00+00:00",
        },
    )
    assert response.status_code == 201
    artifact = response.json()
    if materialize:
        response = client.post(
            f"/api/projects/{project_id}/evidence/{artifact['id']}/materialization",
            json={"manifest": manifest},
        )
        assert response.status_code == 201
    return artifact


def generate(
    client: TestClient,
    project_id: str,
    document_type: str,
) -> dict[str, object]:
    response = client.post(
        f"/api/projects/{project_id}/documents/{document_type}/generate",
        json={"revision_reason": f"Generate governed {document_type}."},
    )
    assert response.status_code == 201
    return response.json()


def assert_source_free_provenance(
    document: dict[str, object],
    artifact: dict[str, object],
) -> None:
    assert document["source_id"] is None
    assert document["target_run_id"] is None
    provenance = document["provenance"]
    assert isinstance(provenance, list)
    assert provenance == [
        {
            "kind": "EVIDENCE_ARTIFACT",
            "reference": f"evidence:{artifact['id']}",
            "evidence_kind": artifact["kind"],
            "checksum": artifact["checksum"],
        }
    ]


def test_semantic_generation_remains_blocked_until_evidence_is_materialized(
    tmp_path: Path,
) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    register_semantic_evidence(
        client,
        project_id,
        kind="DEPLOYMENT_RUNTIME",
        origin_id="deployment-unmaterialized",
        materialize=False,
    )

    response = client.post(
        f"/api/projects/{project_id}/documents/INSTALLATION_GUIDE/generate",
        json={"revision_reason": "Attempt before materialization."},
    )

    assert response.status_code == 409
    payload = response.json()["error"]
    assert payload["code"] == "ENTERPRISE_DOCUMENT_GENERATION_BLOCKED"
    assert payload["documentType"] == "INSTALLATION_GUIDE"
    assert payload["policyVersion"] == "document-readiness-v3"
    assert payload["details"][0]["rule_code"] == "INSTALLATION_DEPLOYMENT_EVIDENCE_REQUIRED"


def test_semantic_generation_pack_is_deterministic_source_free_and_traceable(
    tmp_path: Path,
) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])

    journey = register_semantic_evidence(
        client,
        project_id,
        kind="USER_JOURNEY",
        origin_id="journey-v1",
    )
    deployment = register_semantic_evidence(
        client,
        project_id,
        kind="DEPLOYMENT_RUNTIME",
        origin_id="deployment-v1",
    )
    uat = register_semantic_evidence(
        client,
        project_id,
        kind="UAT_RESULT",
        origin_id="uat-v1",
    )

    user_guide = generate(client, project_id, "USER_GUIDE")
    journey_map = generate(client, project_id, "JOURNEY_MAP")
    installation = generate(client, project_id, "INSTALLATION_GUIDE")
    uat_evidence = generate(client, project_id, "UAT_EVIDENCE")

    assert_source_free_provenance(user_guide, journey)
    assert_source_free_provenance(journey_map, journey)
    assert_source_free_provenance(installation, deployment)
    assert_source_free_provenance(uat_evidence, uat)

    user_content = str(user_guide["content"])
    assert "# User Guide: Semantic Generation" in user_content
    assert "Submit the checkout form." in user_content
    assert "The order is accepted." in user_content
    assert "No UI label, screen, or action is invented." in user_content

    journey_content = str(journey_map["content"])
    assert "# Journey Map: Semantic Generation" in journey_content
    assert "## Journey sequence" in journey_content
    assert "persona" in journey_content.lower()
    assert "No persona, emotion, channel, or stage is invented." in journey_content

    installation_content = str(installation["content"])
    assert "# Installation Guide: Semantic Generation" in installation_content
    assert "**staging**" in installation_content
    assert "| api | 1.4.0 |" in installation_content
    assert "`DATABASE_URL`" in installation_content
    assert "Apply the approved deployment bundle." in installation_content
    assert "Configuration values and secrets are never rendered." in installation_content
    assert "postgres://" not in installation_content

    uat_content = str(uat_evidence["content"])
    assert "# UAT Evidence: Semantic Generation" in uat_content
    assert "Total scenarios: **2**" in uat_content
    assert "Passed: **1**" in uat_content
    assert "Blocked: **1**" in uat_content
    assert "`UAT-001`" in uat_content
    assert "Environment dependency was unavailable." in uat_content

    duplicate = generate(client, project_id, "INSTALLATION_GUIDE")
    assert duplicate["id"] == installation["id"]
    assert duplicate["version"] == installation["version"]
    assert duplicate["reused_existing_version"] is True


def test_semantic_generation_documents_reuse_existing_document_lifecycle(
    tmp_path: Path,
) -> None:
    client = build_client(tmp_path)
    project = create_project(client)
    project_id = str(project["id"])
    register_semantic_evidence(
        client,
        project_id,
        kind="DEPLOYMENT_RUNTIME",
        origin_id="deployment-lifecycle",
    )

    installation = generate(client, project_id, "INSTALLATION_GUIDE")
    version_id = str(installation["id"])

    submit = client.post(
        f"/api/document-versions/{version_id}/submit-review",
        json={"comment": "Ready for technical review."},
    )
    assert submit.status_code == 200
    assert submit.json()["status"] == "IN_REVIEW"

    listed = client.get(f"/api/projects/{project_id}/documents")
    assert listed.status_code == 200
    types = {item["document_type"] for item in listed.json()["items"]}
    assert "INSTALLATION_GUIDE" in types
