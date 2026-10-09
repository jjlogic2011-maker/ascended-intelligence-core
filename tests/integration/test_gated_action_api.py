import importlib

import pytest

import security.auth as auth
from security.approval_service import ApprovalService
from security.shape import ShapeError


@pytest.fixture
def setup(monkeypatch, tmp_path):
    api = importlib.import_module("api.app")
    monkeypatch.setattr(auth, "API_KEY", "agent-key")
    monkeypatch.setattr(auth, "APPROVER_KEY", "approver-key")
    monkeypatch.setattr(api, "PENDING", {})
    clock = [100.0]
    service = ApprovalService(tmp_path / "approvals.db", verify_human=auth.approver_identity,
                              clock=lambda: clock[0])
    monkeypatch.setitem(api.app.config, "APPROVAL_SERVICE", service)
    api.app.config["TESTING"] = True
    with api.app.test_client() as client:
        yield client, api, service, clock


AGENT = {"x-api-key": "agent-key"}
APPROVER = {"x-approver-key": "approver-key"}


def submit(client, action="production-deploy"):
    return client.post("/action", headers=AGENT, json={
        "action": action, "resource": "staging", "arguments": {"commit": "abc"},
        "agent_id": "api-agent", "requester_id": "api-agent",
    })


def issue(service, record):
    return service.issue(credential="approver-key", request_id=record["pending_id"],
                         requester_id=record["requester_id"], action=record["action"],
                         resource=record["resource"], arguments=record["arguments"])


def test_ungated_executes(setup):
    client, _, _, _ = setup
    response = submit(client, "read")
    assert response.status_code == 200
    assert response.json["executed"] is True
    assert response.json["evidence"]["result"]["simulated"] is True


def test_gated_pending_and_listing(setup):
    client, _, _, _ = setup
    response = submit(client)
    assert response.status_code == 202
    assert response.json["status"] == "pending_approval"
    pending = client.get("/approvals", headers=APPROVER).json
    assert [r["pending_id"] for r in pending] == [response.json["pending_id"]]


def test_agent_cannot_approve_or_list(setup):
    client, _, _, _ = setup
    pending_id = submit(client).json["pending_id"]
    assert client.post(f"/approve/{pending_id}", headers=AGENT,
                       json={"approval_id": "fake"}).status_code == 401
    assert client.get("/approvals", headers=AGENT).status_code == 401
    assert client.post(f"/deny/{pending_id}", headers=AGENT).status_code == 401


def test_invalid_approval_is_denied(setup):
    client, api, _, _ = setup
    pending_id = submit(client).json["pending_id"]
    response = client.post(f"/approve/{pending_id}", headers=APPROVER,
                           json={"approval_id": "fake"})
    assert response.status_code == 403
    assert response.json["executed"] is False
    assert api.LEDGER.events[-1].event_type == "DENIED"
    assert api.PENDING[pending_id]["status"] == "failed"
    assert client.get("/approvals", headers=APPROVER).json == []
    assert client.post(f"/approve/{pending_id}", headers=APPROVER,
                       json={"approval_id": "another"}).status_code == 403


def test_valid_approval_executes_once_with_receipt(setup):
    client, api, service, _ = setup
    pending_id = submit(client).json["pending_id"]
    approval_id = issue(service, api.PENDING[pending_id])
    response = client.post(f"/approve/{pending_id}", headers=APPROVER,
                           json={"approval_id": approval_id})
    assert response.status_code == 200
    assert response.json["executed"] is True
    assert response.json["evidence"]["human_approver"] == "api-approver"
    assert api.LEDGER.events[-1].event_id == response.json["receipt_event_id"]
    assert api.LEDGER.verify()[0]
    assert client.post(f"/approve/{pending_id}", headers=APPROVER,
                       json={"approval_id": approval_id}).status_code == 403
    other_id = submit(client).json["pending_id"]
    assert client.post(f"/approve/{other_id}", headers=APPROVER,
                       json={"approval_id": approval_id}).status_code == 403


def test_deny_writes_receipt_and_blocks_approval(setup):
    client, api, service, _ = setup
    pending_id = submit(client).json["pending_id"]
    approval_id = issue(service, api.PENDING[pending_id])
    response = client.post(f"/deny/{pending_id}", headers=APPROVER)
    assert response.status_code == 200
    assert api.PENDING[pending_id]["status"] == "denied"
    assert api.LEDGER.events[-1].event_type == "DENIED"
    assert client.get("/approvals", headers=APPROVER).json == []
    assert client.post(f"/approve/{pending_id}", headers=APPROVER,
                       json={"approval_id": approval_id}).status_code == 403


@pytest.mark.parametrize("failure", ["expired", "revoked", "arguments"])
def test_invalidated_scope_or_approval(setup, failure):
    client, api, service, clock = setup
    pending_id = submit(client).json["pending_id"]
    approval_id = issue(service, api.PENDING[pending_id])
    if failure == "expired":
        clock[0] = 400
    elif failure == "revoked":
        service.revoke(approval_id)
    else:
        api.PENDING[pending_id]["arguments"] = {"commit": "changed"}
    assert client.post(f"/approve/{pending_id}", headers=APPROVER,
                       json={"approval_id": approval_id}).status_code == 403


def test_equal_keys_fail_closed(setup, monkeypatch):
    client, _, _, _ = setup
    monkeypatch.setattr(auth, "APPROVER_KEY", auth.API_KEY)
    assert client.get("/approvals", headers={"x-approver-key": "agent-key"}).status_code == 401


def test_missing_approver_key_fails_closed(setup, monkeypatch):
    client, _, _, _ = setup
    monkeypatch.setattr(auth, "APPROVER_KEY", None)
    assert client.get("/approvals", headers=APPROVER).status_code == 401


def test_unknown_action_and_bad_identity_rejected(setup):
    client, _, _, _ = setup
    assert submit(client, "unknown").status_code == 403
    assert client.post("/action", headers=AGENT, json={
        "action": "read", "resource": "staging", "arguments": {},
        "agent_id": "api-agent", "requester_id": "different",
    }).status_code == 403
    assert client.post("/action", json={}).status_code == 401


def test_self_approval_rejected_at_issuance(setup):
    client, api, service, _ = setup
    pending_id = submit(client).json["pending_id"]
    record = dict(api.PENDING[pending_id], requester_id="api-approver")
    with pytest.raises(ShapeError):
        issue(service, record)
