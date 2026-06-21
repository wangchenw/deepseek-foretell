import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_chat_requires_user_id_in_dev(client, dev_env):
    response = client.post("/v1/chat", json={"message": "hello"})
    assert response.status_code == 401


def test_chat_rejects_foreign_thread_id(client, dev_env):
    response = client.post(
        "/v1/chat",
        headers={"X-User-Id": "user-a"},
        json={"message": "hello", "thread_id": "user-b:abc123"},
    )
    assert response.status_code == 403
