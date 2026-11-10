import pytest
from security.ledger import LivingLedger
from security.authority import issue_grant
from security.dispatcher import ExecutionDispatcher
from security.reliability import ReliabilityController

def test_quarantined_agent_blocked_from_dispatch():
    ledger = LivingLedger()
    controller = ReliabilityController(ledger, max_failures=2)
    dispatcher = ExecutionDispatcher(ledger, reliability_controller=controller)
    
    # Issue a valid grant
    grant = issue_grant(principal_id="alice", agent_id="agent-1", scope={"execute"})
    
    # 1. First execution succeeds (quota is fine)
    res1 = dispatcher.dispatch("req-1", "execute", grant)
    assert res1.success is True
    
    # 2. Simulate two failures for agent-1
    controller.record_failure("agent-1")
    controller.record_failure("agent-1")
    
    # 3. Next execution must be blocked by the Reliability Controller
    res2 = dispatcher.dispatch("req-2", "execute", grant)
    assert res2.success is False
    assert "quarantined" in res2.message
    
    # 4. Verify the ledger recorded the quarantine
    assert any(e.event_type == "AGENT_QUARANTINED" for e in ledger.events)
