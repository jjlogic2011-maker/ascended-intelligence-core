"""Gate 3b.3 - artifact identity resolution at submission and review.

Critical property: a stored identifier is not proof of a live reference.
The artifact must resolve at review time, not just at submission.
"""

import pytest

from security.correction_propagation import (
    CorrectionRegistry,
    LineageGraph,
)
from security.governed_correction import (
    ArtifactNotFound,
    ArtifactRegistry,
    EvidenceRegistry,
    record_review,
    submit_artifact_bound_correction,
    submit_governed_correction,
)


def build_graph():
    g = LineageGraph()
    g.add_edge("dataset", "modelA", material=True)
    return g


def make_registries(artifact_ids=("art-001",), evidence_ids=("ev-001",)):
    evidence = EvidenceRegistry()
    for eid in evidence_ids:
        evidence.register(eid)
    artifacts = ArtifactRegistry()
    for aid in artifact_ids:
        artifacts.register(aid)
    return evidence, artifacts


def submit_ok(artifacts=None, evidence=None, submitted_by="agent-alpha"):
    evidence = evidence or EvidenceRegistry()
    artifacts = artifacts or ArtifactRegistry()
    if "ev-001" not in evidence._ids:
        evidence.register("ev-001")
    if "art-001" not in artifacts._ids:
        artifacts.register("art-001")
    return submit_artifact_bound_correction(
        CorrectionRegistry(), build_graph(),
        origin="dataset", reason="label leakage",
        origin_artifact_id="art-001", artifact_registry=artifacts,
        source_evidence_id="ev-001", evidence_registry=evidence,
        submitted_by=submitted_by,
    )


def test_submission_with_valid_artifact_succeeds():
    governed = submit_ok()
    assert governed.origin_artifact_id == "art-001"


def test_unresolvable_artifact_raises_at_submission():
    evidence, artifacts = make_registries(artifact_ids=())
    with pytest.raises(ArtifactNotFound):
        submit_artifact_bound_correction(
            CorrectionRegistry(), build_graph(),
            origin="dataset", reason="label leakage",
            origin_artifact_id="art-missing", artifact_registry=artifacts,
            source_evidence_id="ev-001", evidence_registry=evidence,
        )


def test_empty_artifact_raises_at_submission():
    evidence, artifacts = make_registries()
    with pytest.raises(ArtifactNotFound):
        submit_artifact_bound_correction(
            CorrectionRegistry(), build_graph(),
            origin="dataset", reason="label leakage",
            origin_artifact_id="", artifact_registry=artifacts,
            source_evidence_id="ev-001", evidence_registry=evidence,
        )


def test_review_succeeds_when_artifact_still_resolves():
    governed = submit_ok()
    result = record_review(governed, reviewed_by="agent-beta", decision="approved")
    assert result.review_state == "approved"


def test_review_fails_if_artifact_removed_after_submission():
    """THE falsification test for the field-presence gap."""
    evidence, artifacts = make_registries()
    governed = submit_ok(artifacts=artifacts, evidence=evidence)
    artifacts._ids.discard("art-001")
    with pytest.raises(ArtifactNotFound):
        record_review(governed, reviewed_by="agent-beta", decision="approved")


def test_review_fails_for_unbound_correction():
    evidence, _ = make_registries()
    governed = submit_governed_correction(
        CorrectionRegistry(), build_graph(),
        origin="dataset", reason="label leakage",
        source_evidence_id="ev-001", evidence_registry=evidence,
        submitted_by="agent-alpha",
    )
    with pytest.raises(ArtifactNotFound):
        record_review(governed, reviewed_by="agent-beta", decision="approved")


def test_review_fails_for_fabricated_registry_binding():
    governed = submit_ok()
    governed._artifact_registry = None
    with pytest.raises(ArtifactNotFound):
        record_review(governed, reviewed_by="agent-beta", decision="approved")
