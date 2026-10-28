"""Unit tests for CAS approval helpers (no Flask)."""
import tempfile
from pathlib import Path

from security.approval_cas import claim_for_processing, do_deny_cas
from security.pending_store import PendingStore


def _store(tmp: str) -> PendingStore:
    return PendingStore(tmp)


def test_claim_for_processing_one_winner(tmp_path):
    db = str(tmp_path / "p.sqlite3")
    store = _store(db)
    pid = "p1"
    store.put(
        pid,
        {
            "pending_id": pid,
            "status": "pending_approval",
            "action": "production-deploy",
            "agent_id": "api-agent",
            "requester_id": "api-agent",
            "resource": "staging",
            "arguments": {},
        },
    )
    a = claim_for_processing(store, pid)
    b = claim_for_processing(store, pid)
    assert a is not None
    assert b is None
    assert store.get(pid)["status"] == "processing"


def test_do_deny_cas(tmp_path):
    db = str(tmp_path / "p.sqlite3")
    store = _store(db)
    pid = "p2"
    store.put(
        pid,
        {
            "pending_id": pid,
            "status": "pending_approval",
            "action": "production-deploy",
            "agent_id": "api-agent",
            "requester_id": "api-agent",
            "resource": "staging",
            "arguments": {},
        },
    )

    class R:
        event_id = "evt-1"

    body, status = do_deny_cas(
        store=store, pending_id=pid, audit=lambda rec, et: R()
    )
    assert status == 200
    assert body["status"] == "denied"
    assert store.get(pid)["status"] == "denied"
