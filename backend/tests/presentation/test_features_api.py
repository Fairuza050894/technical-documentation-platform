from pathlib import Path

from fastapi.testclient import TestClient

from tdp.config import Settings
from tdp.main import create_app


def build_client(database_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                database_path=database_path,
                artifact_root_path=database_path.parent / "artifacts",
            )
        )
    )


def create_workspace_and_project(client: TestClient) -> tuple[dict[str, object], dict[str, object]]:
    workspace = client.post(
        "/api/workspaces",
        json={"key": "ERP", "name": "ERP Workspace", "description": "ERP systems"},
    ).json()
    project = client.post(
        f"/api/workspaces/{workspace['id']}/projects",
        json={
            "key": "ERP-CORE",
            "name": "ERP Core",
            "description": "Core ERP capabilities",
            "ownership_type": "TEAM",
        },
    ).json()
    return workspace, project


def test_feature_registry_and_documentation_map(tmp_path: Path) -> None:
    client = build_client(tmp_path / "feature-api.sqlite3")
    workspace, project = create_workspace_and_project(client)
    base_path = f"/api/workspaces/{workspace['id']}/projects/{project['id']}/features"

    response = client.post(
        base_path,
        json={
            "key": "PAYMENT",
            "name": "Payment Processing",
            "description": "Payment capture and verification",
            "kind": "FEATURE",
            "owner": "ERP Team",
        },
    )

    assert response.status_code == 201
    feature = response.json()
    assert feature["documentation_coverage"] == {
        "required_total": 4,
        "available_required": 0,
        "missing_required": 4,
        "optional_total": 4,
    }

    listed = client.get(base_path)
    assert listed.status_code == 200
    assert listed.json()["items"] == [feature]

    documentation_map = client.get(f"{base_path}/{feature['id']}/documentation-map")
    assert documentation_map.status_code == 200
    assert documentation_map.json()["policy_key"] == "feature-documentation-baseline-v1"
    assert documentation_map.json()["total"] == 8


def test_feature_key_is_unique_inside_project(tmp_path: Path) -> None:
    client = build_client(tmp_path / "feature-key.sqlite3")
    workspace, project = create_workspace_and_project(client)
    base_path = f"/api/workspaces/{workspace['id']}/projects/{project['id']}/features"
    payload = {
        "key": "PAYMENT",
        "name": "Payment Processing",
        "description": "",
        "kind": "FEATURE",
        "owner": "ERP Team",
    }

    assert client.post(base_path, json=payload).status_code == 201
    duplicate = client.post(base_path, json=payload)

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "FEATURE_KEY_ALREADY_EXISTS"


def test_archived_project_blocks_feature_mutation(tmp_path: Path) -> None:
    client = build_client(tmp_path / "feature-read-only.sqlite3")
    workspace, project = create_workspace_and_project(client)
    assert client.post(f"/api/projects/{project['id']}/archive").status_code == 200

    response = client.post(
        f"/api/workspaces/{workspace['id']}/projects/{project['id']}/features",
        json={
            "key": "BLOCKED",
            "name": "Blocked Feature",
            "description": "",
            "kind": "FEATURE",
            "owner": "ERP Team",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "FEATURE_PROJECT_ARCHIVED"
