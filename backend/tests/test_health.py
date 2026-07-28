from fastapi.testclient import TestClient

from tdp.main import create_app


def test_health_endpoint_returns_service_metadata() -> None:
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Technical Documentation Platform",
        "version": "0.1.0",
        "environment": "development",
    }
    assert response.headers["X-Request-ID"]


def test_health_endpoint_preserves_supplied_request_id() -> None:
    client = TestClient(create_app())

    response = client.get("/api/health", headers={"X-Request-ID": "audit-request-001"})

    assert response.headers["X-Request-ID"] == "audit-request-001"
