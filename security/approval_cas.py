"""CAS helpers for pending approval transitions.

Use these from api/app.py approve/deny paths so concurrent workers sharing
one PendingStore SQLite file get single-winner semantics via claim_status.
"""
from __future__ import annotations

from typing import Any, Callable, Optional


def claim_for_processing(store, pending_id: str) -> Optional[dict]:
    return store.claim_status(pending_id, "pending_approval", "processing")


def claim_for_deny(store, pending_id: str) -> Optional[dict]:
    return store.claim_status(pending_id, "pending_approval", "denied")


def claim_for_failed(store, pending_id: str) -> Optional[dict]:
    return store.claim_status(pending_id, "pending_approval", "failed")


def do_approve_cas(
    *,
    store,
    pending_id: str,
    approval_id: str,
    run_action: Callable,
    audit: Callable,
    asdict_fn: Callable,
) -> tuple[dict, int]:
    record = claim_for_processing(store, pending_id)
    if record is None:
        return {"reason": "No active pending request"}, 403
    try:
        result = run_action(record, approval_id)
    except Exception:
        store.update_status(pending_id, "failed")
        audit(record, "DENIED")
        return {"reason": "Approval processing failed; request closed"}, 403
    store.update_status(pending_id, "executed" if result.executed else "failed")
    return asdict_fn(result), 200 if result.executed else 403


def do_deny_cas(* , store, pending_id: str, audit: Callable) -> tuple[dict, int]:
    record = claim_for_deny(store, pending_id)
    if record is None:
        return {"reason": "No active pending request"}, 403
    receipt = audit(record, "DENIED")
    return {
        "status": "denied",
        "pending_id": pending_id,
        "receipt_event_id": receipt.event_id,
    }, 200
