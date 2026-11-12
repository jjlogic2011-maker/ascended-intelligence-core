"""Governed correction submission and review.

Governance requirements layered over CorrectionRegistry:

  1. source_evidence_id resolves against an evidence registry
  2. origin_artifact_id resolves against an artifact registry
  3. artifact re-resolves at review time, not only at submission
  4. reviewer is independent of submitter (separation of duty)
  5. reviewed corrections must have resolved artifact identity

Scope: reference resolution and separation of duty. Proves identifiers
resolve at both submission and review. Does not prove evidence supports
the correction, or that the reviewer had authority. Those are Gate 3c.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from security.correction_propagation import (
    Correction,
    CorrectionRegistry,
    LineageGraph,
)


class GovernanceError(Exception):
    """Raised when a governance requirement is not met."""


class EvidenceNotFound(GovernanceError):
    """Raised when source_evidence_id does not resolve."""


class ArtifactNotFound(GovernanceError):
    """Raised when origin_artifact_id does not resolve, at submit or review."""


class SeparationOfDutyError(GovernanceError):
    """Raised when the reviewer is the submitter."""


@dataclass
class EvidenceRegistry:
    _ids: set = field(default_factory=set)

    def register(self, evidence_id: str) -> None:
        self._ids.add(evidence_id)

    def resolve(self, evidence_id: str) -> bool:
        return evidence_id in self._ids


@dataclass
class ArtifactRegistry:
    _ids: set = field(default_factory=set)

    def register(self, artifact_id: str) -> None:
        self._ids.add(artifact_id)

    def resolve(self, artifact_id: str) -> bool:
        return artifact_id in self._ids


@dataclass
class GovernedCorrection:
    correction: Correction
    submitted_by: str
    source_evidence_id: str
    origin_artifact_id: Optional[str] = None
    _artifact_registry: Optional[ArtifactRegistry] = field(
        default=None, repr=False
    )
    reviewed_by: Optional[str] = None
    review_state: str = "pending"

    def __getattr__(self, name):
        return getattr(self.correction, name)


def submit_governed_correction(
    registry: CorrectionRegistry,
    graph: LineageGraph,
    *,
    origin: str,
    reason: str,
    source_evidence_id: str,
    evidence_registry: EvidenceRegistry,
    submitted_by: str = "unspecified",
    correction_id: Optional[str] = None,
) -> GovernedCorrection:
    """Submit only if source evidence resolves. Does not bind an artifact."""
    if not source_evidence_id or not source_evidence_id.strip():
        raise EvidenceNotFound("source_evidence_id is required")

    if not evidence_registry.resolve(source_evidence_id):
        raise EvidenceNotFound(
            f"source_evidence_id '{source_evidence_id}' not found in evidence registry"
        )

    correction = registry.register(
        graph, origin, reason, correction_id=correction_id,
    )

    return GovernedCorrection(
        correction=correction,
        submitted_by=submitted_by,
        source_evidence_id=source_evidence_id,
    )


def submit_artifact_bound_correction(
    registry: CorrectionRegistry,
    graph: LineageGraph,
    *,
    origin: str,
    reason: str,
    origin_artifact_id: str,
    artifact_registry: ArtifactRegistry,
    source_evidence_id: str,
    evidence_registry: EvidenceRegistry,
    submitted_by: str = "unspecified",
    correction_id: Optional[str] = None,
) -> GovernedCorrection:
    """Submit only if artifact and evidence both resolve. Fails closed."""
    if not origin_artifact_id or not origin_artifact_id.strip():
        raise ArtifactNotFound("origin_artifact_id is required")

    if not artifact_registry.resolve(origin_artifact_id):
        raise ArtifactNotFound(
            f"origin_artifact_id '{origin_artifact_id}' not found in artifact registry"
        )

    governed = submit_governed_correction(
        registry, graph,
        origin=origin,
        reason=reason,
        source_evidence_id=source_evidence_id,
        evidence_registry=evidence_registry,
        submitted_by=submitted_by,
        correction_id=correction_id,
    )
    governed.origin_artifact_id = origin_artifact_id
    governed._artifact_registry = artifact_registry
    return governed


def record_review(
    governed: GovernedCorrection,
    *,
    reviewed_by: str,
    decision: str,
) -> GovernedCorrection:
    """Record a review decision with all governance checks enforced.

    Re-resolves the artifact reference at review time. A stored nonempty
    identifier is not sufficient evidence that the referenced artifact
    still exists.
    """
    if governed.submitted_by == "unspecified":
        raise SeparationOfDutyError(
            "submitted_by must be explicit before review"
        )

    if governed.origin_artifact_id is None:
        raise ArtifactNotFound(
            "correction has no origin artifact; use submit_artifact_bound_correction"
        )

    if governed._artifact_registry is None:
        raise ArtifactNotFound(
            "no artifact registry bound to this correction; cannot verify"
        )

    if not governed._artifact_registry.resolve(governed.origin_artifact_id):
        raise ArtifactNotFound(
            f"origin_artifact_id '{governed.origin_artifact_id}' no longer resolves"
        )

    if not reviewed_by or not reviewed_by.strip():
        raise GovernanceError("reviewed_by is required")

    if governed.submitted_by == reviewed_by:
        raise SeparationOfDutyError(
            f"reviewer '{reviewed_by}' is the submitter"
        )

    if decision not in ("approved", "rejected"):
        raise GovernanceError(f"invalid decision: {decision!r}")

    governed.reviewed_by = reviewed_by
    governed.review_state = decision
    return governed
