"""TrustOS pending_requests store — SQLite-backed, restart-safe.

Replaces the in-memory PENDING dict in api/app.py so that pending
approval requests survive process restart and are visible across
worker processes that share the same database file.

Research module. Production multi-host use should migrate to Postgres.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from typing import Optional


class PendingStore:
    """SQLite-backed store for pending approval requests.

    Records are JSON blobs with at least: pending_id, status, action,
    agent_id, requester_id, resource, arguments.
    """

    def __init__(self, path: str):
        self.path = str(path)
        self._lock = threading.RLock()
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS pending_requests (
                    pending_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    record_json TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )"""
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=10)

    def put(self, pending_id: str, record: dict) -> None:
        if record.get("pending_id") != pending_id:
            raise ValueError("pending_id mismatch")
        if "status" not in record:
            raise ValueError("record must include status")
        with self._lock, self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT OR REPLACE INTO pending_requests VALUES (?, ?, ?, strftime('%s','now'))",
                (
                    pending_id,
                    record["status"],
                    json.dumps(record, sort_keys=True, allow_nan=False),
                ),
            )

    def get(self, pending_id: str) -> Optional[dict]:
        with self._lock, self._connect() as db:
            row = db.execute(
                "SELECT record_json FROM pending_requests WHERE pending_id=?",
                (pending_id,),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def update_status(self, pending_id: str, new_status: str) -> bool:
        with self._lock, self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT record_json FROM pending_requests WHERE pending_id=?",
                (pending_id,),
            ).fetchone()
            if row is None:
                return False
            record = json.loads(row[0])
            record["status"] = new_status
            db.execute(
                "UPDATE pending_requests SET status=?, record_json=?, updated_at=strftime('%s','now') WHERE pending_id=?",
                (new_status, json.dumps(record, sort_keys=True, allow_nan=False), pending_id),
            )
            return True

    def list_pending(self) -> list:
        with self._lock, self._connect() as db:
            rows = db.execute(
                "SELECT record_json FROM pending_requests WHERE status='pending_approval'"
            ).fetchall()
        return [json.loads(r[0]) for r in rows]

    def delete(self, pending_id: str) -> None:
        with self._lock, self._connect() as db:
            db.execute("DELETE FROM pending_requests WHERE pending_id=?", (pending_id,))

    def clear(self) -> None:
        with self._lock, self._connect() as db:
            db.execute("DELETE FROM pending_requests")
