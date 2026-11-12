"""Governed correction submission and review.

Wraps CorrectionRegistry with governance requirements that the
mechanism does not enforce:

  1. source_evidence_id must resolve against an evidence registry
  2. reviewer must be independent of submitter (separation of duty)
  3. review decision must be explicit and valid

Scope: reference resolution and separation of duty. It proves the
reviewer is different from the submitter. It does not prove the
reviewer had the authority to approve, or that the evidence
supports the correction.
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
class GovernedCorrection:
    """Correction with governance metadata attached.

    Delegates attribute access to the inner Correction so existing
    callers using .correction_id or .dispositions continue to work.
    """

    correction: Correction
    submitted_by: str
    source_evidence_id: str
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
    """Submit only if source evidence resolves. Fails closed."""
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


def record_review(
    governed: GovernedCorrection,
    *,
    reviewed_by: str,
    decision: str,
) -> GovernedCorrection:
    """Record a review decision with separation-of-duty enforcement.

    Raises if:
      - submitted_by is 'unspecified' (identity must be explicit)
      - reviewed_by equals submitted_by
      - decision is not 'approved' or 'rejected'
    """
    if governed.submitted_by == "unspecified":
        raise SeparationOfDutyError(
            "submitted_by must be explicit before review; 'unspecified' cannot be reviewed"
        )

    if not reviewed_by or not reviewed_by.strip():
        raise GovernanceError("reviewed_by is required")

    if governed.submitted_by == reviewed_by:
        raise SeparationOfDutyError(
            f"reviewer '{reviewed_by}' is the submitter; independent review required"
        )

    if decision not in ("approved", "rejected"):
        raise GovernanceError(f"invalid decision: {decision!r}")

    governed.reviewed_by = reviewed_by
    governed.review_state = decision
    return governed
