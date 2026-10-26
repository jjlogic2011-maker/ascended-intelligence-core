import time
import threading
import pytest
from security.authority import issue_grant
from security.dispatcher import ExecutionDispatcher
from security.ledger import LivingLedger

@pytest.fixture
def setup():
    ledger = LivingLedger()
    dispatcher = ExecutionDispatcher(ledger)
    grant = issue_grant(principal_id="alice", agent_id="agent-a", scope={"execute"}, max_uses=1)
    return dispatcher, grant, ledger

def test_r01_revoked_before_dispatch(setup):
    dispatcher, grant, ledger = setup
    grant.revoke()
    result = dispatcher.dispatch("req-1", "deploy", grant)
    assert result.success is False
    assert "revoked" in result.message
    assert ledger.events[-1].event_type == "DISPATCH_BLOCKED_REVOKED"

def test_r03_concurrent_revocation_and_execution(setup):
    dispatcher, grant, ledger = setup
    results = []
    def attempt_dispatch():
        results.append(dispatcher.dispatch("req-race", "deploy", grant).success)
    def attempt_revoke():
        time.sleep(0.01) 
        grant.revoke()

    t1 = threading.Thread(target=attempt_dispatch)
    t2 = threading.Thread(target=attempt_revoke)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    ok, errors = ledger.verify()
    assert ok, errors

def test_r06_idempotency(setup):
    dispatcher, grant, ledger = setup
    res1 = dispatcher.dispatch("req-idem", "deploy", grant)
    assert res1.success is True
    res2 = dispatcher.dispatch("req-idem", "deploy", grant)
    assert res2.success is False
    assert "Duplicate dispatch" in res2.message
