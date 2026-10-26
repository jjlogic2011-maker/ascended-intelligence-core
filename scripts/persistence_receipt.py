#!/usr/bin/env python3
"""Write ledger event to disk, reload in a fresh process path, verify chain."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from security.ledger import LivingLedger, load_ledger


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--ledger", required=True)
    args = p.parse_args()
    path = Path(args.ledger)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    led = LivingLedger(path=str(path))
    ev = led.append(
        event_type="ASSESSMENT_PERSIST",
        actor="harness",
        agent="assessment",
        request_id="persist-1",
        artifact_id="persistence_receipt",
    )
    ok, errs = led.verify()
    if not ok:
        print("in_memory_verify_failed", errs)
        return 1

    # Simulate restart: new object loads from disk
    reloaded = load_ledger(str(path))
    ok2, errs2 = reloaded.verify()
    if not ok2:
        print("reload_verify_failed", errs2)
        return 1
    if len(reloaded.events) < 1:
        print("no_events_after_reload")
        return 1
    if reloaded.events[0].event_id != ev.event_id:
        print("event_id_mismatch")
        return 1

    print("persistence_receipt_ok", str(path), "events", len(reloaded.events))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
