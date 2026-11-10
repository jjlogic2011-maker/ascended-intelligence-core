from security.ledger import LivingLedger
from security.reliability import ReliabilityController

def test_quarantine_after_failures():
    ledger = LivingLedger()
    controller = ReliabilityController(ledger, max_failures=2)
    assert controller.check_quota("agent-1").allowed is True
    controller.record_failure("agent-1")
    assert controller.check_quota("agent-1").allowed is True
    controller.record_failure("agent-1")
    assert controller.check_quota("agent-1").allowed is False
    assert ledger.events[-1].event_type == "AGENT_QUARANTINED"

def test_success_resets_failures():
    ledger = LivingLedger()
    controller = ReliabilityController(ledger, max_failures=2)
    controller.record_failure("agent-1")
    controller.record_failure("agent-1")
    controller.record_success("agent-1")
    assert controller.check_quota("agent-1").allowed is True
