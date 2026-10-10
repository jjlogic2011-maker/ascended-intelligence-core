import pytest

from security.pending_store import PendingStore


@pytest.fixture
def store(tmp_path):
    return PendingStore(tmp_path / "pending.sqlite3")


def _record(pending_id, status="pending_approval"):
    return {
        "pending_id": pending_id,
        "status": status,
        "action": "production-deploy",
        "agent_id": "api-agent",
        "requester_id": "api-agent",
        "resource": "staging",
        "arguments": {"commit": "abc"},
    }


def test_put_and_get(store):
    store.put("p1", _record("p1"))
    r = store.get("p1")
    assert r is not None
    assert r["pending_id"] == "p1"
    assert r["status"] == "pending_approval"


def test_get_unknown_returns_none(store):
    assert store.get("nope") is None


def test_update_status(store):
    store.put("p1", _record("p1"))
    ok = store.update_status("p1", "denied")
    assert ok is True
    r = store.get("p1")
    assert r["status"] == "denied"


def test_update_unknown_returns_false(store):
    assert store.update_status("nope", "denied") is False


def test_list_pending_only_lists_active(store):
    store.put("p1", _record("p1"))
    store.put("p2", _record("p2", status="executed"))
    store.put("p3", _record("p3", status="denied"))
    pending = store.list_pending()
    assert [r["pending_id"] for r in pending] == ["p1"]


def test_restart_simulation(tmp_path):
    """A fresh store instance against the same file sees previous data."""
    path = tmp_path / "pending.sqlite3"
    store1 = PendingStore(path)
    store1.put("p1", _record("p1"))
    # Simulate process restart
    store2 = PendingStore(path)
    assert store2.get("p1") is not None
    assert store2.get("p1")["status"] == "pending_approval"


def test_put_rejects_pending_id_mismatch(store):
    with pytest.raises(ValueError):
        store.put("p1", _record("p2"))


def test_clear_removes_all(store):
    store.put("p1", _record("p1"))
    store.put("p2", _record("p2"))
    store.clear()
    assert store.list_pending() == []
    assert store.get("p1") is None
