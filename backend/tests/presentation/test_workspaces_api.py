from pathlib import Path

from fastapi.testclient import TestClient

from tdp.config import Settings
from tdp.main import create_app
from tdp.modules.workspaces.domain.model import DEFAULT_WORKSPACE_ID


def build_client(database_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                database_path=database_path,
                artifact_root_path=database_path.parent / "artifacts",
            )
        )
    )


def test_workspace_registry_and_scoped_projects(tmp_path: Path) -> None:
    client = build_client(tmp_path / "workspace-api.sqlite3")

    initial = client.get("/api/workspaces")
    assert initial.status_code == 200
    assert initial.json()["items"][0]["id"] == DEFAULT_WORKSPACE_ID

    created_response = client.post(
        "/api/workspaces",
        json={
            "key": "ERP",
            "name": "ERP Workspace",
            "description": "ERP systems and integrations",
        },
    )
    assert created_response.status_code == 201
    workspace = created_response.json()

    project_response = client.post(
        f"/api/workspaces/{workspace['id']}/projects",
        json={
            "key": "ERP-CORE",
            "name": "ERP Core",
            "description": "Core ERP capabilities",
            "ownership_type": "TEAM",
        },
    )
    assert project_response.status_code == 201
    project = project_response.json()
    assert project["workspace_id"] == workspace["id"]
    assert project["ownership_type"] == "TEAM"

    scoped = client.get(f"/api/workspaces/{workspace['id']}/projects")
    assert scoped.status_code == 200
    assert scoped.json()["items"] == [project]

    default_scoped = client.get(f"/api/workspaces/{DEFAULT_WORKSPACE_ID}/projects")
    assert default_scoped.status_code == 200
    assert default_scoped.json()["items"] == []


def test_archived_workspace_rejects_new_project(tmp_path: Path) -> None:
    client = build_client(tmp_path / "workspace-archive.sqlite3")
    workspace = client.post(
        "/api/workspaces",
        json={"key": "ARCHIVE", "name": "Archive Workspace", "description": ""},
    ).json()
    assert client.post(f"/api/workspaces/{workspace['id']}/archive").status_code == 200

    response = client.post(
        f"/api/workspaces/{workspace['id']}/projects",
        json={
            "key": "BLOCKED",
            "name": "Blocked Project",
            "description": "",
            "ownership_type": "TEAM",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "WORKSPACE_ARCHIVED"


def test_archived_workspace_makes_project_source_intake_read_only(tmp_path: Path) -> None:
    client = build_client(tmp_path / "workspace-read-only.sqlite3")
    workspace = client.post(
        "/api/workspaces",
        json={"key": "ERP", "name": "ERP Workspace", "description": ""},
    ).json()
    project = client.post(
        f"/api/workspaces/{workspace['id']}/projects",
        json={
            "key": "ERP-CORE",
            "name": "ERP Core",
            "description": "",
            "ownership_type": "TEAM",
        },
    ).json()
    assert client.post(f"/api/workspaces/{workspace['id']}/archive").status_code == 200

    response = client.post(
        f"/api/projects/{project['id']}/sources/openapi",
        data={"name": "ERP OpenAPI"},
        files={
            "file": (
                "erp.yaml",
                b"openapi: 3.1.0\ninfo:\n  title: ERP API\n  version: 1.0.0\npaths: {}\n",
                "application/yaml",
            )
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SOURCE_PROJECT_ARCHIVED"


def test_archived_workspace_rejects_project_archive(tmp_path: Path) -> None:
    client = build_client(tmp_path / "workspace-project-read-only.sqlite3")
    workspace = client.post(
        "/api/workspaces",
        json={"key": "GOVERNED", "name": "Governed Workspace", "description": ""},
    ).json()
    project = client.post(
        f"/api/workspaces/{workspace['id']}/projects",
        json={
            "key": "GOV-PROJECT",
            "name": "Governed Project",
            "description": "",
            "ownership_type": "TEAM",
        },
    ).json()
    assert client.post(f"/api/workspaces/{workspace['id']}/archive").status_code == 200

    response = client.post(f"/api/projects/{project['id']}/archive")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "WORKSPACE_ARCHIVED"
