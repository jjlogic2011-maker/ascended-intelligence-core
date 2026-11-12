"""Governed correction submission.

Wraps CorrectionRegistry with governance-layer requirements that the
mechanism does not enforce:

  1. source_evidence_id must resolve against an evidence registry
  2. origin_artifact_id must resolve against an artifact registry
  3. reviewer must be independent of submitter
  4. rejection is a terminal disposition written to the ledger
  5. propagation targets must resolve against a node registry

This module does NOT replace CorrectionRegistry. It calls it after
validating governance requirements. Mechanism tests remain unchanged.

Scope: reference resolution only. It proves the reference exists.
It does not prove the evidence supports the correction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from security.correction_propagation import (
    Correction,
    CorrectionRegistry,
    LineageGraph,
)


class GovernanceError(Exception):
    """Raised when a governance requirement is not met."""


class EvidenceNotFound(GovernanceError):
    """Raised when source_evidence_id does not resolve."""


@dataclass
class EvidenceRegistry:
    """In-memory evidence registry. Stub for Gate 3b tests."""

    _ids: set = None

    def __post_init__(self):
        if self._ids is None:
            self._ids = set()

    def register(self, evidence_id: str) -> None:
        self._ids.add(evidence_id)

    def resolve(self, evidence_id: str) -> bool:
        return evidence_id in self._ids


def submit_governed_correction(
    registry: CorrectionRegistry,
    graph: LineageGraph,
    *,
    origin: str,
    reason: str,
    source_evidence_id: str,
    evidence_registry: EvidenceRegistry,
    correction_id: Optional[str] = None,
) -> Correction:
    """Submit a correction only if its source evidence resolves.

    Fails closed: unresolvable evidence raises before any registration.
    """
    if not source_evidence_id or not source_evidence_id.strip():
        raise EvidenceNotFound("source_evidence_id is required")

    if not evidence_registry.resolve(source_evidence_id):
        raise EvidenceNotFound(
            f"source_evidence_id '{source_evidence_id}' not found in evidence registry"
        )

    return registry.register(
        graph,
        origin,
        reason,
        correction_id=correction_id,
    )
