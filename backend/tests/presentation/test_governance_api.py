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


def create_workspace_project_feature(
    client: TestClient,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    workspace = client.post(
        "/api/workspaces",
        json={"key": "OPS", "name": "Operations", "description": "Operations"},
    ).json()
    project = client.post(
        f"/api/workspaces/{workspace['id']}/projects",
        json={
            "key": "DRIVER",
            "name": "Driver Platform",
            "description": "Driver operations",
            "ownership_type": "TEAM",
        },
    ).json()
    feature = client.post(
        f"/api/workspaces/{workspace['id']}/projects/{project['id']}/features",
        json={
            "key": "MEAL",
            "name": "Meal Allowance",
            "description": "Driver meal allowance",
            "kind": "FEATURE",
            "owner": "Operations",
        },
    ).json()
    return workspace, project, feature


def test_requirement_trace_impact_and_human_review_api(tmp_path: Path) -> None:
    client = build_client(tmp_path / "governance-api.sqlite3")
    workspace, project, feature = create_workspace_project_feature(client)
    base = f"/api/workspaces/{workspace['id']}/projects/{project['id']}/governance"

    created = client.post(
        f"{base}/requirements",
        json={
            "key": "REQ-MEAL-001",
            "kind": "FUNCTIONAL",
            "title": "Calculate meal allowance",
            "statement": "The system shall calculate meal allowance from the approved driver policy.",
            "acceptance_criteria": ["Calculation uses the active policy version."],
            "owner": "Operations",
        },
    )
    assert created.status_code == 201
    requirement = created.json()
    assert requirement["revision"] == 1

    linked = client.post(
        f"{base}/trace-links",
        json={
            "requirement_revision_id": requirement["id"],
            "target_type": "FEATURE",
            "target_id": feature["id"],
            "relation": "IMPLEMENTED_BY",
            "rationale": "Feature implements the requirement.",
        },
    )
    assert linked.status_code == 201

    evaluated = client.post(
        f"{base}/impacts/evaluate",
        json={
            "change_reference": "commit:meal-policy-v2",
            "changed_target_type": "FEATURE",
            "changed_target_id": feature["id"],
        },
    )
    assert evaluated.status_code == 201
    impact = evaluated.json()
    assert impact["severity"] == "MEDIUM"
    assert impact["impacted_requirement_ids"] == [requirement["id"]]
    assert "REVIEW_IMPLEMENTATION" in impact["required_actions"]
    assert impact["workflow_state"] == "OPEN"

    invalid_approval = client.post(
        f"{base}/impacts/{impact['id']}/transitions",
        json={"action": "APPROVE", "comment": "Cannot skip review."},
    )
    assert invalid_approval.status_code == 409
    assert invalid_approval.json()["error"]["code"] == "INVALID_WORKFLOW_TRANSITION"

    submitted = client.post(
        f"{base}/impacts/{impact['id']}/transitions",
        json={"action": "SUBMIT", "comment": "Ready for review."},
    )
    assert submitted.status_code == 200
    assert submitted.json()["assessment"]["workflow_state"] == "IN_REVIEW"

    approved = client.post(
        f"{base}/impacts/{impact['id']}/transitions",
        json={"action": "APPROVE", "comment": "Trace impact reviewed."},
    )
    assert approved.status_code == 200
    assert approved.json()["assessment"]["workflow_state"] == "APPROVED"

    events = client.get(f"{base}/impacts/{impact['id']}/events")
    assert events.status_code == 200
    assert [item["action"] for item in events.json()["items"]] == ["SUBMIT", "APPROVE"]
    assert all(item["actor"] for item in events.json()["items"])


def test_requirement_revision_api_is_append_only(tmp_path: Path) -> None:
    client = build_client(tmp_path / "requirement-revision.sqlite3")
    workspace, project, _ = create_workspace_project_feature(client)
    base = f"/api/workspaces/{workspace['id']}/projects/{project['id']}/governance"

    first = client.post(
        f"{base}/requirements",
        json={
            "key": "REQ-TRACK-001",
            "kind": "BUSINESS",
            "title": "Track shipment activity",
            "statement": "Operations shall have an auditable view of shipment activity progression.",
            "acceptance_criteria": [],
            "owner": "Operations",
        },
    ).json()
    second_response = client.post(
        f"{base}/requirements/REQ-TRACK-001/revisions",
        json={
            "title": "Track shipment activity and exceptions",
            "statement": "Operations shall have an auditable view of shipment activity and exceptions.",
            "acceptance_criteria": ["Exceptions remain linked to source evidence."],
            "owner": "Operations",
        },
    )
    assert second_response.status_code == 201
    second = second_response.json()
    assert second["revision"] == 2
    assert second["previous_revision_id"] == first["id"]

    latest = client.get(f"{base}/requirements")
    assert latest.status_code == 200
    assert latest.json()["total"] == 1
    assert latest.json()["items"][0]["id"] == second["id"]
