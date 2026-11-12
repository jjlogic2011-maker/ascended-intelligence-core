"""Gate 3b — evidence reference resolution tests.

Criterion: a correction cannot be submitted without source evidence
that resolves against an evidence registry.
"""

import pytest

from security.correction_propagation import (
    CorrectionRegistry,
    LineageGraph,
)
from security.governed_correction import (
    EvidenceNotFound,
    EvidenceRegistry,
    submit_governed_correction,
)


def build_graph():
    g = LineageGraph()
    g.add_edge("dataset", "modelA", material=True)
    return g


def test_submission_with_valid_evidence_succeeds():
    registry = CorrectionRegistry()
    evidence = EvidenceRegistry()
    evidence.register("ev-2026-001")

    correction = submit_governed_correction(
        registry,
        build_graph(),
        origin="dataset",
        reason="label leakage",
        source_evidence_id="ev-2026-001",
        evidence_registry=evidence,
        correction_id="corr-ev-ok",
    )

    assert correction.correction_id == "corr-ev-ok"
    assert "modelA" in correction.dispositions


def test_submission_with_unresolvable_evidence_raises():
    registry = CorrectionRegistry()
    evidence = EvidenceRegistry()

    with pytest.raises(EvidenceNotFound):
        submit_governed_correction(
            registry,
            build_graph(),
            origin="dataset",
            reason="label leakage",
            source_evidence_id="ev-does-not-exist",
            evidence_registry=evidence,
        )


def test_submission_with_empty_evidence_raises():
    registry = CorrectionRegistry()
    evidence = EvidenceRegistry()

    with pytest.raises(EvidenceNotFound):
        submit_governed_correction(
            registry,
            build_graph(),
            origin="dataset",
            reason="label leakage",
            source_evidence_id="",
            evidence_registry=evidence,
        )


def test_failed_submission_does_not_register_correction():
    """Fail-closed: unresolvable evidence must not leave a partial correction."""
    registry = CorrectionRegistry()
    evidence = EvidenceRegistry()

    with pytest.raises(EvidenceNotFound):
        submit_governed_correction(
            registry,
            build_graph(),
            origin="dataset",
            reason="label leakage",
            source_evidence_id="ev-missing",
            evidence_registry=evidence,
            correction_id="corr-must-not-exist",
        )

    # Attempting to register the same ID again must succeed
    # because the first attempt never created it
    evidence.register("ev-missing")
    correction = submit_governed_correction(
        registry,
        build_graph(),
        origin="dataset",
        reason="label leakage",
        source_evidence_id="ev-missing",
        evidence_registry=evidence,
        correction_id="corr-must-not-exist",
    )
    assert correction.correction_id == "corr-must-not-exist"
