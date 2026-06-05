from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_endpoint_returns_stable_payload() -> None:
    client = TestClient(app)

    response = client.get("/api/health", headers={"X-Request-ID": "test-request-id"})

    assert response.status_code == 200
    assert response.json() == {
        "service": "HiFleetAI",
        "status": "ok",
        "api_version": "v1",
    }
    assert response.headers["X-Request-ID"] == "test-request-id"
