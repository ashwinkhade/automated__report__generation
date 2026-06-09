"""Auth/API smoke tests using SQLite in-memory DB."""
import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    # Reset DB
    if os.path.exists("test.db"):
        os.remove("test.db")
    from backend.main import app
    from backend.core.database import init_db
    init_db()
    return TestClient(app)


def test_register_and_login(client):
    r = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "username": "tester",
        "password": "secret123",
        "full_name": "Test User",
    })
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    assert token

    r2 = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    assert r2.json()["username"] == "tester"


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
