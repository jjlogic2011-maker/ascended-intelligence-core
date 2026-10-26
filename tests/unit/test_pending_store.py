import multiprocessing as mp

import pytest

from security.pending_store import PendingStore


def _claim_status_worker(db_path, out_q):
    store = PendingStore(db_path)
    result = store.claim_status("p1", "pending_approval", "processing")
    out_q.put(result is not None)


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
    path = tmp_path / "pending.sqlite3"
    store1 = PendingStore(path)
    store1.put("p1", _record("p1"))
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


def test_claim_status_success(store):
    store.put("p1", _record("p1"))
    claimed = store.claim_status("p1", "pending_approval", "processing")
    assert claimed is not None
    assert claimed["status"] == "processing"
    assert store.get("p1")["status"] == "processing"


def test_claim_status_fails_when_not_pending(store):
    store.put("p1", _record("p1", status="failed"))
    assert store.claim_status("p1", "pending_approval", "processing") is None
    assert store.get("p1")["status"] == "failed"


def test_claim_status_only_one_winner_multiprocess(tmp_path):
    """Two processes share one SQLite file; exactly one claim succeeds."""
    path = str(tmp_path / "race.sqlite3")
    store = PendingStore(path)
    store.put("p1", _record("p1"))

    q: mp.Queue = mp.Queue()
    procs = [
        mp.Process(target=_claim_status_worker, args=(path, q)) for _ in range(2)
    ]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=15)
        assert p.exitcode == 0

    wins = [q.get(timeout=5), q.get(timeout=5)]
    assert wins.count(True) == 1
    assert wins.count(False) == 1
    assert PendingStore(path).get("p1")["status"] == "processing"
