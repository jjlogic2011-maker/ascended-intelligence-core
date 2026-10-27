"""Synthetic external effect sink for TrustOS race and finality tests.

Provides an independently observable commit surface separate from the
Living Ledger. A ledger DISPATCH_SUCCESS is not proof of external effect;
this module is.

Optional path: when constructed with a filesystem path, commits survive
process restart (R06-B). Default in-memory mode is for unit tests only.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any


class SyntheticExternalDB:
    """Observable effect store. Idempotent per request_id."""

    def __init__(self, path: str | None = None):
        self._path = Path(path) if path else None
        self._lock = threading.RLock()
        self._effects: dict[str, dict[str, Any]] = {}
        if self._path and self._path.exists():
            data = json.loads(self._path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self._effects = data

    def _persist(self) -> None:
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(self._effects, sort_keys=True, indent=0),
            encoding="utf-8",
        )
        tmp.replace(self._path)

    def commit_effect(self, request_id: str, action: str) -> dict[str, Any]:
        """Commit or return existing effect for request_id (idempotent)."""
        with self._lock:
            if request_id in self._effects:
                return dict(self._effects[request_id])
            record = {
                "request_id": request_id,
                "action": action,
                "committed": True,
            }
            self._effects[request_id] = record
            self._persist()
            return dict(record)

    def has_effect(self, request_id: str) -> bool:
        with self._lock:
            return request_id in self._effects

    def get_effect(self, request_id: str) -> dict[str, Any] | None:
        with self._lock:
            rec = self._effects.get(request_id)
            return dict(rec) if rec else None

    def clear(self) -> None:
        with self._lock:
            self._effects.clear()
            if self._path and self._path.exists():
                self._path.unlink()


# Process-default sink used by ExecutionDispatcher (tests may replace).
EXTERNAL_DB = SyntheticExternalDB()
