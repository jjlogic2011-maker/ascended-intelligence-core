"""Integration tests: /noi001/command routes through live governance."""
import importlib

import pytest


@pytest.fixture
def setup(monkeypatch, tmp_path):
    monkeypatch.setenv("AICI_API_KEY", "agent-key")
    monkeypatch.setenv("AICI_APPROVER_KEY", "approver-key")
    monkeypatch.setenv("AICI_UI_KEY", "ui-key")
    monkeypatch.setenv("AICI_UI_SECRET", "test-secret")
    monkeypatch.setenv("AICI_PENDING_DB", str(tmp_path / "pending.sqlite3"))
    monkeypatch.setenv("AICI_APPROVAL_DB", str(tmp_path / "approvals.sqlite3"))
    import security.auth as auth
    auth.API_KEY = "agent-key"
    auth.APPROVER_KEY = "approver-key"
    api = importlib.import_module("api.app")
    monkeypatch.setitem(api.app.config, "PENDING_STORE", None)
    api.app.config["TESTING"] = True
    api.app.secret_key = "test-secret"
    with api.app.test_client() as client:
        yield client, api


AGENT = {"x-api-key": "agent-key"}


def test_recognized_command_returns_recognized_true(setup):
    client, _ = setup
    r = client.post("/noi001/command", headers=AGENT,
                    json={"command": "show status"})
    assert r.status_code in (200, 202)
    body = r.get_json()
    assert body["recognized"] is True
    assert body["visual"].startswith("[STATUS]")


def test_unrecognized_command_is_denied(setup):
    client, _ = setup
    r = client.post("/noi001/command", headers=AGENT,
                    json={"command": "blow up the world"})
    assert r.status_code == 400
    body = r.get_json()
    assert body["recognized"] is False
    assert "Unrecognized" in body["reason"]


@pytest.mark.parametrize("bad", [None, "", "   ", 123, [], {}])
def test_missing_or_invalid_command_fails_closed(setup, bad):
    client, _ = setup
    r = client.post("/noi001/command", headers=AGENT,
                    json={"command": bad})
    assert r.status_code == 400
    assert r.get_json()["recognized"] is False


def test_route_returns_request_id_and_visual(setup):
    client, _ = setup
    r = client.post("/noi001/command", headers=AGENT,
                    json={"command": "show status"})
    body = r.get_json()
    assert body.get("request_id") or body.get("receipt_event_id")
    assert body.get("visual")
    assert body["visual"].startswith("[")
    assert body.get("latency_ms") is not None


def test_governance_denial_surfaced_without_pretending_execution(setup):
    """Gated command returns 202, not executed=true."""
    client, _ = setup
    r = client.post("/noi001/command", headers=AGENT,
                    json={"command": "request deploy"})
    assert r.status_code == 202
    body = r.get_json()
    assert body["recognized"] is True
    assert body["executed"] is False
    assert body["status"] == "pending_approval"
    assert body["pending_id"]
    assert body["decision"] == "PENDING"


def test_unauthorized_request_rejected(setup):
    client, _ = setup
    r = client.post("/noi001/command", json={"command": "show status"})
    assert r.status_code == 401
    assert r.get_json()["recognized"] is False


def test_all_five_vocabulary_commands_recognized(setup):
    client, _ = setup
    for cmd in ["show status", "log intention", "clear display",
                "record coherence", "abort"]:
        r = client.post("/noi001/command", headers=AGENT,
                        json={"command": cmd})
        body = r.get_json()
        assert body["recognized"] is True, f"failed on {cmd!r}"
        assert body["decision"] in ("EXECUTED", "PENDING", "DENIED")


def test_extra_json_keys_rejected(setup):
    client, _ = setup
    r = client.post("/noi001/command", headers=AGENT,
                    json={"command": "show status", "extra": "no"})
    assert r.status_code == 400
    assert r.get_json()["recognized"] is False
