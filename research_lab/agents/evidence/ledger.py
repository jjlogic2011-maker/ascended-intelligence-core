"""
Living Evidence Ledger — append-only, hash-chained log of agent actions,
claims, diagrams, reports, and verification results.

Every entry is timestamped, classified, and linked to prior state.
This is the proof trail: "what was claimed, what was run, what was verified."
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


EVIDENCE_DIR = Path(__file__).resolve().parents[2] / "evidence_logs"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
LEDGER_FILE = EVIDENCE_DIR / "living_evidence_ledger.jsonl"


@dataclass
class EvidenceEntry:
    entry_id: str
    timestamp: float
    agent: str
    action: str
    claim: Optional[str] = None
    classification: str = "UNSPECIFIED"
    evidence_type: str = "log"
    payload: Dict[str, Any] = field(default_factory=dict)
    prior_hash: str = ""
    entry_hash: str = ""
    status: str = "recorded"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _hash_entry(data: Dict[str, Any]) -> str:
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _last_hash() -> str:
    if not LEDGER_FILE.exists():
        return "GENESIS"
    last = None
    with LEDGER_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last = json.loads(line)
    return last.get("entry_hash", "GENESIS") if last else "GENESIS"


def append_evidence(
    agent: str,
    action: str,
    *,
    claim: Optional[str] = None,
    classification: str = "OPERATIONAL",
    evidence_type: str = "log",
    payload: Optional[Dict[str, Any]] = None,
    status: str = "recorded",
) -> EvidenceEntry:
    prior = _last_hash()
    ts = time.time()
    entry_id = hashlib.sha256(f"{agent}:{action}:{ts}".encode()).hexdigest()[:16]

    raw = {
        "entry_id": entry_id,
        "timestamp": ts,
        "agent": agent,
        "action": action,
        "claim": claim,
        "classification": classification,
        "evidence_type": evidence_type,
        "payload": payload or {},
        "prior_hash": prior,
        "status": status,
    }
    entry_hash = _hash_entry(raw)
    raw["entry_hash"] = entry_hash

    entry = EvidenceEntry(**raw)
    with LEDGER_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry.to_dict(), default=str) + "\n")
    return entry


def read_ledger(limit: int = 50) -> List[Dict[str, Any]]:
    if not LEDGER_FILE.exists():
        return []
    entries = []
    with LEDGER_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries[-limit:]


def ledger_summary() -> Dict[str, Any]:
    entries = read_ledger(limit=1000)
    by_agent: Dict[str, int] = {}
    by_class: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    for e in entries:
        by_agent[e["agent"]] = by_agent.get(e["agent"], 0) + 1
        by_class[e["classification"]] = by_class.get(e["classification"], 0) + 1
        by_status[e["status"]] = by_status.get(e["status"], 0) + 1
    return {
        "total_entries": len(entries),
        "by_agent": by_agent,
        "by_classification": by_class,
        "by_status": by_status,
        "ledger_path": str(LEDGER_FILE),
        "tip_hash": entries[-1]["entry_hash"] if entries else "GENESIS",
    }
