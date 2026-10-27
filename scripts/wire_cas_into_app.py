#!/usr/bin/env python3
"""Rewrite api/app.py approve/deny helpers to use security.approval_cas.

Run from repo root after pulling this branch:
  python scripts/wire_cas_into_app.py
"""
from __future__ import annotations

from pathlib import Path

APP = Path("api/app.py")

OLD_CLAIM = '''def _claim_pending(pending_id):
    """Active pending record, or None. Caller must hold PENDING_LOCK."""
    record = _pending_store().get(pending_id)
    if record is None or record["status"] != "pending_approval":
        return None
    return record'''

NEW_CLAIM = '''def _claim_pending(pending_id):
    """Atomically claim pending_approval -> processing via CAS, or None."""
    return _pending_store().claim_status(
        pending_id, "pending_approval", "processing"
    )'''

OLD_CLOSE = '''def _close_malformed_approval(pending_id):
    """Fail an active request under PENDING_LOCK, then write one DENIED receipt."""
    store = _pending_store()
    with PENDING_LOCK:
        record = _claim_pending(pending_id)
        if record is None:
            return
        store.update_status(pending_id, "failed")
        _action_audit(record, "DENIED")'''

NEW_CLOSE = '''def _close_malformed_approval(pending_id):
    """CAS-claim pending_approval -> failed; one DENIED receipt."""
    store = _pending_store()
    with PENDING_LOCK:
        record = store.claim_status(pending_id, "pending_approval", "failed")
        if record is None:
            return
        _action_audit(record, "DENIED")'''

OLD_APPROVE = '''def _do_approve(pending_id, approval_id):
    """Shared approve logic. Returns (body_dict, http_status)."""
    store = _pending_store()
    with PENDING_LOCK:
        record = _claim_pending(pending_id)
        if record is None:
            return {"reason": "No active pending request"}, 403
        store.update_status(pending_id, "processing")
    try:
        result = _run_action(record, approval_id)
    except Exception:
        store.update_status(pending_id, "failed")
        _action_audit(record, "DENIED")
        return {"reason": "Approval processing failed; request closed"}, 403
    store.update_status(pending_id, "executed" if result.executed else "failed")
    return asdict(result), 200 if result.executed else 403'''

NEW_APPROVE = '''def _do_approve(pending_id, approval_id):
    """Shared approve logic. CAS claim then execute."""
    store = _pending_store()
    with PENDING_LOCK:
        record = _claim_pending(pending_id)
        if record is None:
            return {"reason": "No active pending request"}, 403
    try:
        result = _run_action(record, approval_id)
    except Exception:
        store.update_status(pending_id, "failed")
        _action_audit(record, "DENIED")
        return {"reason": "Approval processing failed; request closed"}, 403
    store.update_status(pending_id, "executed" if result.executed else "failed")
    return asdict(result), 200 if result.executed else 403'''

OLD_DENY = '''def _do_deny(pending_id):
    """Shared deny logic. Returns (body_dict, http_status)."""
    store = _pending_store()
    with PENDING_LOCK:
        record = _claim_pending(pending_id)
        if record is None:
            return {"reason": "No active pending request"}, 403
        receipt = _action_audit(record, "DENIED")
        store.update_status(pending_id, "denied")
    return {
        "status": "denied",
        "pending_id": pending_id,
        "receipt_event_id": receipt.event_id,
    }, 200'''

NEW_DENY = '''def _do_deny(pending_id):
    """Shared deny logic. CAS claim pending_approval -> denied."""
    store = _pending_store()
    with PENDING_LOCK:
        record = store.claim_status(pending_id, "pending_approval", "denied")
        if record is None:
            return {"reason": "No active pending request"}, 403
        receipt = _action_audit(record, "DENIED")
    return {
        "status": "denied",
        "pending_id": pending_id,
        "receipt_event_id": receipt.event_id,
    }, 200'''


def main() -> None:
    text = APP.read_text(encoding="utf-8")
    pairs = [
        (OLD_CLAIM, NEW_CLAIM),
        (OLD_CLOSE, NEW_CLOSE),
        (OLD_APPROVE, NEW_APPROVE),
        (OLD_DENY, NEW_DENY),
    ]
    for old, new in pairs:
        if old not in text:
            if new[:40] in text:
                print("already applied:", new.split(chr(10))[0])
                continue
            raise SystemExit("pattern not found: " + old[:60])
        text = text.replace(old, new, 1)
    if "AICI_LEDGER_PATH" not in text and "LEDGER = LivingLedger()\n" in text:
        text = text.replace(
            "LEDGER = LivingLedger()\n",
            '_ledger_path = os.getenv("AICI_LEDGER_PATH")\n'
            "LEDGER = LivingLedger(path=_ledger_path) if _ledger_path else LivingLedger()\n",
            1,
        )
    APP.write_text(text, encoding="utf-8")
    print("wired CAS into", APP)


if __name__ == "__main__":
    main()
