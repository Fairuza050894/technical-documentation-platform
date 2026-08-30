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


class TestScannerListEndpoint:
    def test_list_scans_empty(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        response = client.get("/api/scanner/scans")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


class TestScannerStartEndpoint:
    def test_start_scan_returns_pending(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        response = client.post(
            "/api/scanner/scan",
            json={
                "repository_url": "https://github.com/octocat/Hello-World.git",
                "branch": "master",
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "PENDING"
        assert data["repository_name"] == "Hello-World"
        assert data["branch"] == "master"
        assert "id" in data

    def test_start_scan_appears_in_list(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        start_response = client.post(
            "/api/scanner/scan",
            json={"repository_url": "https://github.com/octocat/Hello-World.git"},
        )
        scan_id = start_response.json()["id"]

        list_response = client.get("/api/scanner/scans")
        assert list_response.status_code == 200
        ids = [s["id"] for s in list_response.json()["items"]]
        assert scan_id in ids


class TestScannerGetEndpoint:
    def test_get_scan_by_id(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        start_response = client.post(
            "/api/scanner/scan",
            json={"repository_url": "https://github.com/octocat/Hello-World.git"},
        )
        scan_id = start_response.json()["id"]

        get_response = client.get(f"/api/scanner/scans/{scan_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == scan_id

    def test_get_nonexistent_scan_returns_404(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        response = client.get("/api/scanner/scans/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


class TestScannerDeleteEndpoint:
    def test_delete_scan(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        start_response = client.post(
            "/api/scanner/scan",
            json={"repository_url": "https://github.com/octocat/Hello-World.git"},
        )
        scan_id = start_response.json()["id"]

        delete_response = client.delete(f"/api/scanner/scans/{scan_id}")
        assert delete_response.status_code == 204

        get_response = client.get(f"/api/scanner/scans/{scan_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_returns_404(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        response = client.delete("/api/scanner/scans/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


class TestScannerRescanEndpoint:
    def test_rescan_creates_new_scan(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        start_response = client.post(
            "/api/scanner/scan",
            json={"repository_url": "https://github.com/octocat/Hello-World.git"},
        )
        original_id = start_response.json()["id"]

        rescan_response = client.post(f"/api/scanner/scans/{original_id}/rescan")
        assert rescan_response.status_code == 202
        new_id = rescan_response.json()["id"]
        assert new_id != original_id

        list_response = client.get("/api/scanner/scans")
        ids = [s["id"] for s in list_response.json()["items"]]
        assert original_id in ids
        assert new_id in ids

    def test_rescan_nonexistent_returns_404(self, tmp_path: Path) -> None:
        client = build_client(tmp_path / "test.sqlite3")
        response = client.post("/api/scanner/scans/00000000-0000-0000-0000-000000000000/rescan")
        assert response.status_code == 404
