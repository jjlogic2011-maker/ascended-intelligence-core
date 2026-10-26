from security.ledger import LivingLedger
from security.telemetry import TelemetryEngine

def test_telemetry_records_and_verifies():
    ledger = LivingLedger()
    telemetry = TelemetryEngine(ledger)

    telemetry.record_execution("write", "agent-a", "req-1")
    telemetry.record_denial("delete", "agent-b", "unauthorized")

    metrics = telemetry.get_metrics()
    assert metrics["executions"] == 1
    assert metrics["denials"] == 1
    assert metrics["ledger_intact"] is True
    assert ledger.verify()[0] is True
