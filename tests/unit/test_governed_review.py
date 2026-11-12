"""Gate 3b.2 — separation of duty tests.

Criterion: a correction cannot be reviewed by its submitter.
"""

import pytest

from security.correction_propagation import (
    CorrectionRegistry,
    LineageGraph,
)
from security.governed_correction import (
    EvidenceRegistry,
    GovernanceError,
    SeparationOfDutyError,
    record_review,
    submit_governed_correction,
)


def build_graph():
    g = LineageGraph()
    g.add_edge("dataset", "modelA", material=True)
    return g


def make_submission(submitted_by="agent-alpha"):
    registry = CorrectionRegistry()
    evidence = EvidenceRegistry()
    evidence.register("ev-001")
    return submit_governed_correction(
        registry,
        build_graph(),
        origin="dataset",
        reason="label leakage",
        source_evidence_id="ev-001",
        evidence_registry=evidence,
        submitted_by=submitted_by,
    )


def test_independent_reviewer_approves():
    gc = make_submission(submitted_by="agent-alpha")

    result = record_review(gc, reviewed_by="agent-beta", decision="approved")

    assert result.reviewed_by == "agent-beta"
    assert result.review_state == "approved"


def test_independent_reviewer_rejects():
    gc = make_submission(submitted_by="agent-alpha")

    result = record_review(gc, reviewed_by="agent-beta", decision="rejected")

    assert result.review_state == "rejected"


def test_submitter_cannot_review_own_correction():
    gc = make_submission(submitted_by="agent-alpha")

    with pytest.raises(SeparationOfDutyError):
        record_review(gc, reviewed_by="agent-alpha", decision="approved")


def test_unspecified_submitter_cannot_be_reviewed():
    """Forces explicit identity - 'unspecified' is a submission-time hole."""
    gc = make_submission(submitted_by="unspecified")

    with pytest.raises(SeparationOfDutyError):
        record_review(gc, reviewed_by="agent-beta", decision="approved")


def test_invalid_decision_raises():
    gc = make_submission(submitted_by="agent-alpha")

    with pytest.raises(GovernanceError):
        record_review(gc, reviewed_by="agent-beta", decision="maybe")


def test_empty_reviewer_raises():
    gc = make_submission(submitted_by="agent-alpha")

    with pytest.raises(GovernanceError):
        record_review(gc, reviewed_by="", decision="approved")
