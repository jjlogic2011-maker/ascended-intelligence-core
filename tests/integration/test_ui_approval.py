import importlib

import pytest

import security.auth as auth
from security.approval_service import ApprovalService


@pytest.fixture
def setup(monkeypatch, tmp_path):
    monkeypatch.setenv("AICI_UI_KEY", "ui-key")
    monkeypatch.setenv("AICI_UI_SECRET", "test-secret")
    monkeypatch.setenv("AICI_PENDING_DB", str(tmp_path / "pending.sqlite3"))
    api = importlib.import_module("api.app")
    monkeypatch.setattr(auth, "API_KEY", "agent-key")
    monkeypatch.setattr(auth, "APPROVER_KEY", "approver-key")
    monkeypatch.setitem(api.app.config, "PENDING_STORE", None)
    monkeypatch.setitem(api.app.config, "APPROVAL_SERVICE",
        ApprovalService(tmp_path / "approvals.db",
                        verify_human=auth.approver_identity))
    api.app.config["TESTING"] = True
    api.app.secret_key = "test-secret"
    with api.app.test_client() as client:
        yield client, api


AGENT = {"x-api-key": "agent-key"}
APPROVER = {"x-approver-key": "approver-key"}


def submit(client):
    return client.post("/action", headers=AGENT, json={
        "action": "production-deploy", "resource": "staging",
        "arguments": {"commit": "abc"},
        "agent_id": "api-agent", "requester_id": "api-agent",
    })


def login(client):
    return client.post("/ui/login", data={"key": "ui-key"}, follow_redirects=False)


def test_ui_login_with_valid_key(setup):
    client, _ = setup
    r = login(client)
    assert r.status_code in (302, 303)


def test_ui_login_wrong_key_returns_401(setup):
    client, _ = setup
    r = client.post("/ui/login", data={"key": "wrong"}, follow_redirects=False)
    assert r.status_code == 401


def test_ui_index_requires_login(setup):
    client, _ = setup
    r = client.get("/ui", follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/ui/login" in r.headers.get("Location", "")


def test_ui_index_shows_pending(setup):
    client, _ = setup
    submit(client)
    login(client)
    r = client.get("/ui")
    assert r.status_code == 200
    assert b"Pending Approvals" in r.data
    assert b"production-deploy" in r.data


def test_ui_deny_marks_denied(setup):
    client, api = setup
    pending_id = submit(client).get_json()["pending_id"]
    login(client)
    r = client.post(f"/ui/deny/{pending_id}", follow_redirects=False)
    assert r.status_code in (302, 303)
    rec = api._pending_store().get(pending_id)
    assert rec["status"] == "denied"


def test_ui_disabled_when_key_unset(setup, monkeypatch):
    client, _ = setup
    monkeypatch.delenv("AICI_UI_KEY", raising=False)
    r = client.get("/ui/login")
    assert r.status_code == 503


def test_ui_logout_clears_session(setup):
    client, _ = setup
    login(client)
    client.get("/ui/logout", follow_redirects=False)
    r = client.get("/ui", follow_redirects=False)
    assert r.status_code in (302, 303)


def test_ui_approve_with_invalid_id_redirects_with_error(setup):
    client, api = setup
    pending_id = submit(client).get_json()["pending_id"]
    login(client)
    r = client.post(f"/ui/approve/{pending_id}",
                    data={"approval_id": "fake"},
                    follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "message=" in r.headers.get("Location", "")
    rec = api._pending_store().get(pending_id)
    assert rec["status"] == "failed"
