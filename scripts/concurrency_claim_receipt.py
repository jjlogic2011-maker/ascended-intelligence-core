#!/usr/bin/env python3
"""Prove claim_status allows only one winner under concurrent workers."""
from __future__ import annotations

import multiprocessing as mp
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from security.pending_store import PendingStore


def _worker(db_path: str, pending_id: str, q: mp.Queue) -> None:
    store = PendingStore(db_path)
    won = store.claim_status(pending_id, "pending_approval", "processing")
    q.put(won is not None)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="claim-receipt-") as tmp:
        db = str(Path(tmp) / "pending.sqlite3")
        store = PendingStore(db)
        pid = "concurrent-1"
        store.put(
            pid,
            {
                "pending_id": pid,
                "status": "pending_approval",
                "action": "production-deploy",
                "agent_id": "api-agent",
                "requester_id": "api-agent",
                "resource": "staging",
                "arguments": {},
            },
        )
        q: mp.Queue = mp.Queue()
        procs = [
            mp.Process(target=_worker, args=(db, pid, q)) for _ in range(8)
        ]
        for p in procs:
            p.start()
        for p in procs:
            p.join(timeout=30)
        winners = sum(1 for _ in procs if q.get(timeout=5) is True)
        if winners != 1:
            print("concurrency_claim_failed winners=", winners)
            return 1
        final = store.get(pid)
        if not final or final.get("status") != "processing":
            print("final_status_unexpected", final)
            return 1
        print("concurrency_claim_receipt_ok winners=1")
        return 0


if __name__ == "__main__":
    # spawn is safer cross-platform
    try:
        mp.set_start_method("spawn")
    except RuntimeError:
        pass
    raise SystemExit(main())
