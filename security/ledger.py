"""Living Ledger — append-only tamper-evident hash chain.

Each event contains:
    event_id, correlation_id, timestamp, event_type, actor, agent,
    request_id, artifact_id, previous_event_hash, event_hash,
    correction_of

event_hash = SHA-256( canonical_json(fields excluding event_hash) )

Verification detects:
- broken links (previous_event_hash mismatch)
- modified payloads (event_hash mismatch)

This is NOT a blockchain. It is a single-writer, local, append-only
log. No consensus, no proof-of-work, no multi-writer resolution.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid
from dataclasses import asdict, dataclass

GENESIS = "0" * 64


class LedgerError(Exception):
    """Raised on ledger misuse."""


@dataclass(frozen=True)
class LedgerEvent:
    event_id: str
    correlation_id: str
    timestamp: float
    event_type: str
    actor: str
    agent: str
    request_id: str
    artifact_id: str
    correction_of: str | None
    previous_event_hash: str
    event_hash: str

    def to_dict(self) -> dict:
        return asdict(self)


def _compute_event_hash(fields: dict) -> str:
    payload = {k: v for k, v in fields.items() if k != "event_hash"}
    blob = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


class LivingLedger:
    def __init__(self, path: str | None = None):
        self._lock = threading.Lock()
        self._events: list = []
        self._path = path

    @property
    def events(self) -> list:
        return list(self._events)

    def _last_hash(self) -> str:
        return self._events[-1].event_hash if self._events else GENESIS

    def append(
        self,
        *,
        event_type: str,
        actor: str,
        agent: str,
        request_id: str,
        artifact_id: str,
        correlation_id: str | None = None,
        correction_of: str | None = None,
        timestamp: float | None = None,
    ) -> LedgerEvent:
        with self._lock:
            fields = {
                "event_id": str(uuid.uuid4()),
                "correlation_id": correlation_id or str(uuid.uuid4()),
                "timestamp": (
                    timestamp if timestamp is not None else time.time()
                ),
                "event_type": event_type,
                "actor": actor,
                "agent": agent,
                "request_id": request_id,
                "artifact_id": artifact_id,
                "correction_of": correction_of,
                "previous_event_hash": self._last_hash(),
            }
            fields["event_hash"] = _compute_event_hash(fields)
            event = LedgerEvent(**fields)
            self._events.append(event)
            if self._path:
                self._persist(event)
            return event

    def _persist(self, event: LedgerEvent) -> None:
        line = json.dumps(
            event.to_dict(), sort_keys=True, separators=(",", ":")
        )
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def verify(self) -> tuple:
        errors: list = []
        prev = GENESIS
        for i, ev in enumerate(self._events):
            if ev.previous_event_hash != prev:
                errors.append(
                    f"event {i} ({ev.event_id}): previous_event_hash mismatch"
                )
            expected = _compute_event_hash(ev.to_dict())
            if expected != ev.event_hash:
                errors.append(
                    f"event {i} ({ev.event_id}): event_hash mismatch"
                )
            prev = ev.event_hash
        return (not errors), errors


def load_ledger(path: str) -> LivingLedger:
    ledger = LivingLedger(path=None)
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            ledger._events.append(LedgerEvent(**data))
    ledger._path = path
    return ledger
