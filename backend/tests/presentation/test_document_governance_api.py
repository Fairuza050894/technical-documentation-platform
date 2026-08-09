from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from tdp.config import Settings
from tdp.main import create_app


def build_client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                database_path=tmp_path / "governance.sqlite3",
                artifact_root_path=tmp_path / "artifacts",
            )
        )
    )


def _create_project(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/projects",
        json={
            "key": "GOV",
            "name": "Governed Documentation",
            "description": "Enterprise documentation policy.",
            "workspace_type": "PERSONAL",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_document_type_registry_exposes_canonical_enterprise_profiles(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get("/api/document-types")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "document-type-registry-v1"
    assert payload["total"] == 10
    assert [item["document_type"] for item in payload["items"]] == [
        "HLD",
        "LLD",
        "AS_BUILT",
        "SOP",
        "USER_GUIDE",
        "INSTALLATION_GUIDE",
        "PROJECT_HANDOVER",
        "UAT_EVIDENCE",
        "JOURNEY_MAP",
        "DEVELOPER_ONBOARDING_BRIEF",
    ]
    assert payload["items"][0]["automation_profile"] == "HYBRID"
    assert payload["items"][2]["automation_profile"] == "EVIDENCE_DRIVEN"
    assert payload["items"][6]["automation_profile"] == "GOVERNED_BUNDLE"


def test_project_documentation_checklist_is_deterministic_and_readable_when_archived(
    tmp_path: Path,
) -> None:
    client = build_client(tmp_path)
    project = _create_project(client)
    project_id = str(project["id"])

    initial_response = client.get(f"/api/projects/{project_id}/documentation-checklist")
    assert initial_response.status_code == 200
    initial = initial_response.json()
    assert initial["policy_key"] == "project-documentation-baseline-v1"
    assert initial["total"] == 10
    assert initial["required_total"] == 7
    assert initial["supplementary_total"] == 3
    assert initial["available_total"] == 0
    assert initial["missing_required_total"] == 7
    assert all(item["availability"] == "MISSING" for item in initial["items"])

    archive_response = client.post(f"/api/projects/{project_id}/archive")
    assert archive_response.status_code == 200
    assert archive_response.json()["status"] == "ARCHIVED"

    archived_response = client.get(f"/api/projects/{project_id}/documentation-checklist")
    assert archived_response.status_code == 200
    assert archived_response.json() == initial


def test_project_documentation_checklist_rejects_unknown_project(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get(f"/api/projects/{uuid4()}/documentation-checklist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCUMENT_PROJECT_NOT_FOUND"
