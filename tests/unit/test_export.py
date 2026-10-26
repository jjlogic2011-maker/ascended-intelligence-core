from security.ledger import LivingLedger
from security.export import generate_export, verify_export

def test_export_and_verify():
    ledger = LivingLedger()
    ledger.append(event_type="EXECUTED", actor="agent-a", agent="agent-a", request_id="req-123", artifact_id="deploy")
    
    packet = generate_export(ledger, "req-123")
    assert packet is not None
    assert packet["event_count"] == 1
    assert "export_hash" in packet
    
    # Should verify successfully
    assert verify_export(packet.copy()) is True
    
    # Tamper check
    tampered = packet.copy()
    tampered["events"][0]["event_type"] = "HACKED"
    assert verify_export(tampered) is False
