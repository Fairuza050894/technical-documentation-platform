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


def _push_payload(branch="main", sha="abc123"):
    return {
        "ref": f"refs/heads/{branch}",
        "after": sha,
        "head_commit": {"id": sha, "message": "test commit"},
        "repository": {"clone_url": "https://github.com/octocat/Hello-World.git", "name": "Hello-World"},
        "sender": {"login": "testuser"},
    }


def _pr_payload(action="opened", branch="feature"):
    return {
        "action": action,
        "pull_request": {
            "title": "Add feature",
            "head": {"ref": branch, "sha": "def456"},
        },
        "repository": {"clone_url": "https://github.com/octocat/Hello-World.git", "name": "Hello-World"},
        "sender": {"login": "devuser"},
    }


class TestGitHubWebhookEndpoint:
    def test_push_event_accepted(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        response = client.post(
            "/api/scanner/webhooks/github",
            json=_push_payload(),
            headers={"X-GitHub-Event": "push"},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["event_type"] == "push"
        assert data["repository_name"] == "Hello-World"
        assert data["branch"] == "main"
        assert data["status"] == "COMPLETED"
        assert data["scan_id"] != ""

    def test_pr_opened_accepted(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        response = client.post(
            "/api/scanner/webhooks/github",
            json=_pr_payload(action="opened"),
            headers={"X-GitHub-Event": "pull_request"},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["event_type"] == "pull_request"
        assert data["status"] == "COMPLETED"

    def test_pr_closed_skipped(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        response = client.post(
            "/api/scanner/webhooks/github",
            json=_pr_payload(action="closed"),
            headers={"X-GitHub-Event": "pull_request"},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "SKIPPED"

    def test_unsupported_event_returns_202(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        response = client.post(
            "/api/scanner/webhooks/github",
            json={},
            headers={"X-GitHub-Event": "issues"},
        )
        assert response.status_code == 202


class TestWebhookEventsEndpoint:
    def test_list_events_empty(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        response = client.get("/api/scanner/webhooks/events")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_events_after_push(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        client.post(
            "/api/scanner/webhooks/github",
            json=_push_payload(),
            headers={"X-GitHub-Event": "push"},
        )
        response = client.get("/api/scanner/webhooks/events")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["event_type"] == "push"

    def test_get_event_by_id(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        post_response = client.post(
            "/api/scanner/webhooks/github",
            json=_push_payload(),
            headers={"X-GitHub-Event": "push"},
        )
        event_id = post_response.json()["id"]

        get_response = client.get(f"/api/scanner/webhooks/events/{event_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == event_id

    def test_get_nonexistent_event_returns_404(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        response = client.get("/api/scanner/webhooks/events/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
