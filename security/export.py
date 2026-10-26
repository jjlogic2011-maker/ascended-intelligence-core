"""TrustOS Integrity Export.

Generates portable, verifiable JSON receipts for a specific request_id.
Includes a SHA-256 hash of the canonical packet so an external party
can verify the evidence offline without trusting the database.
"""
import json
import hashlib
from security.ledger import LivingLedger

def generate_export(ledger: LivingLedger, request_id: str) -> dict | None:
    events = [e.to_dict() for e in ledger.events if e.request_id == request_id]
    if not events:
        return None
        
    packet = {
        "request_id": request_id,
        "events": events,
        "event_count": len(events)
    }
    
    # Hash the canonical representation
    blob = json.dumps(packet, sort_keys=True, separators=(",", ":")).encode("utf-8")
    packet["export_hash"] = hashlib.sha256(blob).hexdigest()
    return packet

def verify_export(packet: dict) -> bool:
    """Verify the export hash offline."""
    provided_hash = packet.pop("export_hash", None)
    if not provided_hash:
        return False
        
    blob = json.dumps(packet, sort_keys=True, separators=(",", ":")).encode("utf-8")
    expected_hash = hashlib.sha256(blob).hexdigest()
    
    # Put it back so the packet isn't mutated for the caller
    packet["export_hash"] = provided_hash 
    return provided_hash == expected_hash
