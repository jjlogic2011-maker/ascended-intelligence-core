"""Experiment runner and in-memory result store.

Results can later be linked to Living Ledger events.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .quantum import run_chsh_simulation, CHSHResult
from .resonance import generate_and_analyze, ResonanceResult


@dataclass
class ExperimentRecord:
    experiment_id: str
    kind: str  # quantum | resonance | neuroscience
    status: str
    created_at: float
    finished_at: Optional[float]
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    error: Optional[str] = None
    evidence_class: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ExperimentStore:
    def __init__(self) -> None:
        self._records: Dict[str, ExperimentRecord] = {}

    def put(self, record: ExperimentRecord) -> None:
        self._records[record.experiment_id] = record

    def get(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        r = self._records.get(experiment_id)
        return r.to_dict() if r else None

    def list_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        items = sorted(
            self._records.values(), key=lambda r: r.created_at, reverse=True
        )
        return [r.to_dict() for r in items[:limit]]


# Process-wide store for the Flask process
STORE = ExperimentStore()


def run_experiment(kind: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    parameters = parameters or {}
    exp_id = str(uuid.uuid4())
    created = time.time()
    record = ExperimentRecord(
        experiment_id=exp_id,
        kind=kind,
        status="running",
        created_at=created,
        finished_at=None,
        parameters=parameters,
        result=None,
    )
    STORE.put(record)

    try:
        if kind == "quantum":
            n = int(parameters.get("n_trials", 10_000))
            seed = parameters.get("seed", 42)
            if seed is not None:
                seed = int(seed)
            result: CHSHResult = run_chsh_simulation(n_trials=n, seed=seed)
            record.result = result.to_dict()
            record.evidence_class = result.evidence_class
            record.notes = result.notes
        elif kind == "resonance":
            freqs = parameters.get("frequencies_hz")
            sr = int(parameters.get("sample_rate", 44100))
            dur = float(parameters.get("duration_s", 1.0))
            result_r: ResonanceResult = generate_and_analyze(
                frequencies_hz=freqs, sample_rate=sr, duration_s=dur
            )
            record.result = result_r.to_dict()
            record.evidence_class = result_r.evidence_class
            record.notes = result_r.notes
        else:
            raise ValueError(f"Unsupported experiment kind: {kind}")

        record.status = "completed"
        record.finished_at = time.time()
    except Exception as exc:
        record.status = "failed"
        record.error = str(exc)
        record.finished_at = time.time()

    STORE.put(record)
    return record.to_dict()
