import pytest
import security.auth as auth_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(auth_module, "API_KEY", "test-key")
    monkeypatch.setattr(auth_module, "USERNAME", "admin")
    monkeypatch.setattr(auth_module, "PASSWORD", "s3cur3")
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


# --- POST /login ---

def test_login_valid_credentials(client):
    resp = client.post("/login", json={"username": "admin", "password": "s3cur3"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "connected"
    assert body["api_key"] == "test-key"


def test_login_wrong_password_returns_401(client):
    resp = client.post("/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401
    assert "error" in resp.get_json()


def test_login_wrong_username_returns_401(client):
    resp = client.post("/login", json={"username": "hacker", "password": "s3cur3"})
    assert resp.status_code == 401


def test_login_missing_body_returns_401(client):
    resp = client.post("/login")
    assert resp.status_code == 401


def test_login_returned_key_works_for_execute(client):
    login_resp = client.post("/login", json={"username": "admin", "password": "s3cur3"})
    api_key = login_resp.get_json()["api_key"]
    exec_resp = client.post("/execute", json={"type": "report"},
                            headers={"x-api-key": api_key})
    assert exec_resp.status_code == 200
    assert exec_resp.get_json()["status"] == "executed"
