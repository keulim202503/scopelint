import pytest
from fastapi.testclient import TestClient

from scopelint.db import create_team
from scopelint.server import create_app


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "scopelint.db")


@pytest.fixture
def team(db_path):
    return create_team(db_path, "team-a")


@pytest.fixture
def client(db_path):
    return TestClient(create_app(db_path))


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_without_api_key_returns_401(client):
    response = client.post("/ingest", json={"timestamp": "t1", "task": "a", "ok": True, "findings": []})

    assert response.status_code == 401


def test_ingest_with_invalid_api_key_returns_401(client):
    response = client.post(
        "/ingest",
        json={"timestamp": "t1", "task": "a", "ok": True, "findings": []},
        headers={"X-API-Key": "not-a-real-key"},
    )

    assert response.status_code == 401


def test_ingest_with_valid_api_key_returns_201(client, team):
    response = client.post(
        "/ingest",
        json={"timestamp": "t1", "task": "a", "ok": True, "findings": []},
        headers={"X-API-Key": team.api_key},
    )

    assert response.status_code == 201


def test_ingest_persists_check_visible_in_dashboard(client, team):
    client.post(
        "/ingest",
        json={
            "timestamp": "t1",
            "task": "a",
            "ok": False,
            "findings": [{"path": "requirements.txt", "reason": "민감 파일 변경"}],
        },
        headers={"X-API-Key": team.api_key},
    )

    response = client.get("/dashboard", headers={"X-API-Key": team.api_key})

    assert response.status_code == 200
    assert "requirements.txt" in response.text


def test_dashboard_without_api_key_returns_401(client):
    response = client.get("/dashboard")

    assert response.status_code == 401


def test_dashboard_scoped_per_team(client, db_path, team):
    other_team = create_team(db_path, "team-b")
    client.post(
        "/ingest",
        json={"timestamp": "t1", "task": "a", "ok": False, "findings": [{"path": "secret.env", "reason": "x"}]},
        headers={"X-API-Key": team.api_key},
    )

    response = client.get("/dashboard", headers={"X-API-Key": other_team.api_key})

    assert response.status_code == 200
    assert "secret.env" not in response.text
