from pathlib import Path

from fastapi.testclient import TestClient

from tdp.config import Settings
from tdp.main import create_app


def test_current_identity_comes_from_server_configuration(tmp_path: Path) -> None:
    client = TestClient(
        create_app(
            Settings(
                environment="test",
                database_path=tmp_path / "identity.sqlite3",
                artifact_root_path=tmp_path / "artifacts",
                local_identity_subject="reviewer-001",
                local_identity_name="Lead Reviewer",
                local_identity_email="reviewer@example.com",
            )
        )
    )

    response = client.get("/api/identity/me")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "subject_id": "reviewer-001",
        "display_name": "Lead Reviewer",
        "email": "reviewer@example.com",
        "provider": "local",
        "assurance": "DEVELOPMENT",
        "audit_actor": "Lead Reviewer [local:reviewer-001]",
    }
