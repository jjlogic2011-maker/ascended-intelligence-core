import pytest
import security.auth as auth_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(auth_module, "API_KEY", "test-key")
    from api.app import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# --- GET / ---

def test_home_returns_message(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "AICI Core Running"


# --- GET /health ---

def test_health_returns_healthy(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "healthy"


# --- POST /execute auth ---

def test_execute_missing_key_returns_401(client):
    resp = client.post("/execute", json={"type": "report"})
    assert resp.status_code == 401
    assert "error" in resp.get_json()


def test_execute_wrong_key_returns_401(client):
    resp = client.post("/execute", json={"type": "report"},
                       headers={"x-api-key": "wrong"})
    assert resp.status_code == 401


# --- POST /execute payloads ---

def test_execute_report_task(client):
    resp = client.post("/execute", json={"type": "report"},
                       headers={"x-api-key": "test-key"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "executed"
    assert body["result"]["status"] == "success"


def test_execute_security_task(client):
    resp = client.post("/execute", json={"type": "security"},
                       headers={"x-api-key": "test-key"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "executed"
    assert body["result"]["expert"] == "security"


def test_execute_no_body_returns_error(client):
    resp = client.post("/execute", headers={"x-api-key": "test-key"})
    assert resp.status_code == 200
    assert "error" in resp.get_json()


def test_execute_empty_json_returns_error(client):
    resp = client.post("/execute", json=None,
                       headers={"x-api-key": "test-key"})
    assert resp.status_code == 200
    assert "error" in resp.get_json()


def test_execute_default_type_routes_to_report(client):
    resp = client.post("/execute", json={"payload": "no type"},
                       headers={"x-api-key": "test-key"})
    assert resp.status_code == 200
    assert resp.get_json()["result"]["status"] == "success"
