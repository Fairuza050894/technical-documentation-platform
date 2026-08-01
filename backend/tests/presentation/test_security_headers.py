from pathlib import Path

from fastapi.testclient import TestClient

from tdp.config import Settings
from tdp.main import create_app


def test_api_responses_include_baseline_security_headers(tmp_path: Path) -> None:
    client = TestClient(
        create_app(
            Settings(
                environment="test",
                database_path=tmp_path / "security.sqlite3",
                artifact_root_path=tmp_path / "artifacts",
            )
        )
    )

    response = client.get("/api/health/live")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
