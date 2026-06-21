"""Phase 0: FastAPI health endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app


def test_health_returns_200() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
