"""TRUSTOS-RACE-001 acceptance tests — external effect is the oracle."""
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from security.authority import issue_grant
from security.dispatcher import ExecutionDispatcher
from security.external_adapter import SyntheticExternalDB
from security.ledger import LivingLedger


@pytest.fixture
def race_env(tmp_path):
    ledger = LivingLedger()
    external = SyntheticExternalDB(path=str(tmp_path / "effects.json"))
    external.clear()
    processed = str(tmp_path / "processed.json")
    dispatcher = ExecutionDispatcher(
        ledger,
        external_db=external,
        processed_path=processed,
        latency_s=0.05,
    )
    grant = issue_grant(
        principal_id="alice",
        agent_id="agent-a",
        scope={"execute"},
        max_uses=5,
    )
    return dispatcher, grant, ledger, external, processed, tmp_path


def test_r01_revoked_before_dispatch_no_effect(race_env):
    dispatcher, grant, ledger, external, _, _ = race_env
    grant.revoke()
    result = dispatcher.dispatch("req-1", "execute", grant)
    assert result.success is False
    assert external.has_effect("req-1") is False
    assert ledger.events[-1].event_type == "DISPATCH_BLOCKED_REVOKED"


def test_r03_a_revoke_during_dispatch_no_effect(race_env):
    dispatcher, grant, ledger, external, _, _ = race_env

    def revoke():
        time.sleep(0.02)
        grant.revoke()

    t = threading.Thread(target=revoke)
    t.start()
    result = dispatcher.dispatch("req-race-late", "execute", grant)
    t.join()
    assert result.success is False
    assert "revoked during dispatch" in result.message
    assert external.has_effect("req-race-late") is False
    assert ledger.events[-1].event_type == "DISPATCH_ABORTED_LATE_REVOCATION"


def test_r03_b_concurrent_same_request_one_effect(race_env):
    dispatcher, grant, ledger, external, _, _ = race_env
    results = []

    def run():
        results.append(dispatcher.dispatch("req-once", "execute", grant).success)

    threads = [threading.Thread(target=run) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sum(1 for x in results if x) == 1
    assert external.has_effect("req-once") is True
    ok, errors = ledger.verify()
    assert ok, errors


def test_r06_sequential_idempotency(race_env):
    dispatcher, grant, ledger, external, _, _ = race_env
    r1 = dispatcher.dispatch("req-idem", "execute", grant)
    r2 = dispatcher.dispatch("req-idem", "execute", grant)
    assert r1.success is True
    assert r2.success is False
    assert "Duplicate" in r2.message
    assert external.get_effect("req-idem")["action"] == "execute"


def test_r06_b_restart_replay_blocked(race_env):
    dispatcher, grant, ledger, external, processed, tmp_path = race_env
    r1 = dispatcher.dispatch("req-restart", "execute", grant)
    assert r1.success is True
    assert external.has_effect("req-restart") is True

    # New process-equivalent: new dispatcher, same durable paths
    ledger2 = LivingLedger()
    external2 = SyntheticExternalDB(path=str(tmp_path / "effects.json"))
    d2 = ExecutionDispatcher(
        ledger2,
        external_db=external2,
        processed_path=processed,
        latency_s=0.0,
    )
    r2 = d2.dispatch("req-restart", "execute", grant)
    assert r2.success is False
    assert external2.has_effect("req-restart") is True


def test_r06_c_scope_and_exhaustion_no_effect(race_env):
    dispatcher, grant, ledger, external, _, _ = race_env
    res = dispatcher.dispatch("req-scope", "delete", grant)
    assert res.success is False
    assert "out of scope" in res.message
    assert external.has_effect("req-scope") is False

    grant2 = issue_grant(
        principal_id="alice", agent_id="agent-a", scope={"execute"}, max_uses=1
    )
    grant2.used_count = 1
    res2 = dispatcher.dispatch("req-exhaust", "execute", grant2)
    assert res2.success is False
    assert external.has_effect("req-exhaust") is False
