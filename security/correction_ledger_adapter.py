"""Correction-to-ledger adapter.

Records a completed correction in the LivingLedger (fact of the event)
and persists the full correction record in a sidecar envelope (content
of the event), linked by correction_id.

Scope: preserves the tested LivingLedger contract unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path

from security.correction_propagation import Correction, canonical_hash
from security.ledger import LedgerEvent, LivingLedger


def record_correction(
    ledger: LivingLedger,
    correction: Correction,
    *,
    actor: str,
    agent: str,
    request_id: str,
    envelope_dir: str,
    correction_of: str | None = None,
) -> tuple[LedgerEvent, dict]:
    record = correction.to_record()

    event = ledger.append(
        event_type="CORRECTION_RECORDED",
        actor=actor,
        agent=agent,
        request_id=request_id,
        artifact_id=correction.correction_id,
        correction_of=correction_of,
    )

    envelope_path = Path(envelope_dir) / f"{correction.correction_id}.json"
    envelope_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = envelope_path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(record, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    tmp.replace(envelope_path)

    return event, record


def verify_correction(
    ledger: LivingLedger,
    correction_id: str,
    envelope_dir: str,
) -> dict:
    result = {
        "correction_id": correction_id,
        "envelope_present": False,
        "envelope_hash_valid": False,
        "ledger_event_present": False,
        "ledger_chain_valid": False,
        "verified": False,
        "errors": [],
    }

    envelope_path = Path(envelope_dir) / f"{correction_id}.json"
    if not envelope_path.exists():
        result["errors"].append("envelope_missing")
    else:
        result["envelope_present"] = True
        record = json.loads(envelope_path.read_text(encoding="utf-8"))
        stored_hash = record.get("snapshot_sha256")
        body = {k: v for k, v in record.items() if k != "snapshot_sha256"}
        recomputed = canonical_hash(body)
        if recomputed != stored_hash:
            result["errors"].append("envelope_hash_mismatch")
        else:
            result["envelope_hash_valid"] = True

    matching = [
        ev for ev in ledger.events
        if ev.event_type == "CORRECTION_RECORDED"
        and ev.artifact_id == correction_id
    ]
    if not matching:
        result["errors"].append("ledger_event_missing")
    else:
        result["ledger_event_present"] = True

    ok, chain_errors = ledger.verify()
    result["ledger_chain_valid"] = ok
    if not ok:
        result["errors"].extend(chain_errors)

    result["verified"] = (
        result["envelope_present"]
        and result["envelope_hash_valid"]
        and result["ledger_event_present"]
        and result["ledger_chain_valid"]
    )
    return result
