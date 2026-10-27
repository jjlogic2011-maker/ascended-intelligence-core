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
    monkeypatch.setenv("AICI_PENDING_DB", str(tmp_path / "pending.sqlite3"))
    monkeypatch.setitem(api.app.config, "PENDING_STORE", None)
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
    assert api._pending_store().get(pending_id)["status"] == "failed"
    assert client.get("/approvals", headers=APPROVER).json == []
    assert client.post(f"/approve/{pending_id}", headers=APPROVER,
                       json={"approval_id": "another"}).status_code == 403


def test_valid_approval_executes_once_with_receipt(setup):
    client, api, service, _ = setup
    pending_id = submit(client).json["pending_id"]
    approval_id = issue(service, api._pending_store().get(pending_id))
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
    approval_id = issue(service, api._pending_store().get(pending_id))
    response = client.post(f"/deny/{pending_id}", headers=APPROVER)
    assert response.status_code == 200
    assert api._pending_store().get(pending_id)["status"] == "denied"
    assert api.LEDGER.events[-1].event_type == "DENIED"
    assert client.get("/approvals", headers=APPROVER).json == []
    assert client.post(f"/approve/{pending_id}", headers=APPROVER,
                       json={"approval_id": approval_id}).status_code == 403


def test_approval_paths_use_atomic_claim_not_unconditional_write(setup, monkeypatch):
    client, api, service, _ = setup
    store = api._pending_store()
    writes = []
    original = store.update_status

    def record_write(pending_id, new_status):
        writes.append((pending_id, new_status))
        return original(pending_id, new_status)

    monkeypatch.setattr(store, "update_status", record_write)
    pending_id = submit(client).json["pending_id"]
    approval_id = issue(service, store.get(pending_id))
    approved = client.post(f"/approve/{pending_id}", headers=APPROVER,
                           json={"approval_id": approval_id})
    assert approved.status_code == 200
    assert store.get(pending_id)["status"] == "executed"

    denied_id = submit(client).json["pending_id"]
    denied = client.post(f"/deny/{denied_id}", headers=APPROVER)
    assert denied.status_code == 200
    assert store.get(denied_id)["status"] == "denied"

    malformed_id = submit(client).json["pending_id"]
    malformed = client.post(f"/approve/{malformed_id}", headers=APPROVER,
                            data="not-json", content_type="application/json")
    assert malformed.status_code == 403
    assert store.get(malformed_id)["status"] == "failed"
    assert writes == []


@pytest.mark.parametrize("failure", ["expired", "revoked", "arguments"])
def test_invalidated_scope_or_approval(setup, failure):
    client, api, service, clock = setup
    pending_id = submit(client).json["pending_id"]
    approval_id = issue(service, api._pending_store().get(pending_id))
    if failure == "expired":
        clock[0] = 400
    elif failure == "revoked":
        service.revoke(approval_id)
    else:
        _rec = api._pending_store().get(pending_id)

        _rec["arguments"] = {"commit": "changed"}

        api._pending_store().put(pending_id, _rec)
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
    record = dict(api._pending_store().get(pending_id), requester_id="api-approver")
    with pytest.raises(ShapeError):
        issue(service, record)

def _denied_ids(api, pending_id):
    return [
        event.event_id for event in api.LEDGER.events
        if event.event_type == "DENIED" and event.request_id == pending_id
    ]


def _executed_ids(api, pending_id):
    return [
        event.event_id for event in api.LEDGER.events
        if event.event_type == "EXECUTED" and event.request_id == pending_id
    ]


# Raw bodies, not the test client's json= helper. json=None omits the body
# and cannot express JSON null, a JSON array, invalid JSON, or an empty body.
MALFORMED_APPROVAL_BODIES = [
    pytest.param(b"{}", "application/json", id="empty-object"),
    pytest.param(b'{"approval_id":""}', "application/json", id="empty-approval-id"),
    pytest.param(b'{"approval_id":"   "}', "application/json", id="whitespace-approval-id"),
    pytest.param(b'{"approval_id":null}', "application/json", id="null-approval-id"),
    pytest.param(b'{"approval_id":123}', "application/json", id="numeric-approval-id"),
    pytest.param(
        b'{"approval_id":"ok","extra":1}', "application/json", id="unexpected-field",
    ),
    pytest.param(b"null", "application/json", id="json-null"),
    pytest.param(b"[]", "application/json", id="json-array"),
    pytest.param(b"{", "application/json", id="invalid-json"),
    pytest.param(b"", "application/json", id="empty-body"),
]


def _post_approval(client, pending_id, body, content_type, headers):
    return client.post(
        f"/approve/{pending_id}",
        headers=headers,
        data=body,
        content_type=content_type,
    )


@pytest.mark.parametrize("body,content_type", MALFORMED_APPROVAL_BODIES)
def test_malformed_approval_payload_closes_request(setup, body, content_type):
    client, api, service, _ = setup
    pending_id = submit(client).json["pending_id"]
    before = _denied_ids(api, pending_id)
    response = _post_approval(client, pending_id, body, content_type, APPROVER)
    assert response.status_code == 403
    assert response.json["reason"] == "Approval ID required"
    assert api._pending_store().get(pending_id)["status"] == "failed"
    assert client.get("/approvals", headers=APPROVER).json == []
    denied = _denied_ids(api, pending_id)
    assert len(denied) == len(before) + 1
    assert api.LEDGER.verify()[0] is True

    record = api._pending_store().get(pending_id)
    approval_id = issue(service, record)
    follow_up = client.post(
        f"/approve/{pending_id}", headers=APPROVER, json={"approval_id": approval_id},
    )
    assert follow_up.status_code == 403
    assert follow_up.json.get("executed") is not True
    assert api._pending_store().get(pending_id)["status"] == "failed"
    assert _executed_ids(api, pending_id) == []
    assert _denied_ids(api, pending_id) == denied

    retry = _post_approval(client, pending_id, body, content_type, APPROVER)
    assert retry.status_code == 403
    assert api._pending_store().get(pending_id)["status"] == "failed"
    assert _denied_ids(api, pending_id) == denied
    assert _executed_ids(api, pending_id) == []
    assert api.LEDGER.verify()[0] is True


@pytest.mark.parametrize("body,content_type", MALFORMED_APPROVAL_BODIES)
def test_agent_malformed_approval_does_not_mutate(setup, body, content_type):
    client, api, _, _ = setup
    pending_id = submit(client).json["pending_id"]
    before = [event.event_id for event in api.LEDGER.events]
    response = _post_approval(client, pending_id, body, content_type, AGENT)
    assert response.status_code == 401
    assert api._pending_store().get(pending_id)["status"] == "pending_approval"
    assert [event.event_id for event in api.LEDGER.events] == before
    listed = client.get("/approvals", headers=APPROVER).json
    assert [row["pending_id"] for row in listed] == [pending_id]
