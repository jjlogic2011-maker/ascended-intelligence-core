"""Unit tests for evidence registry."""

from research.evidence import EvidenceRegistry, VALID_CLASSES


def test_registry_seeds():
    reg = EvidenceRegistry()
    claims = reg.list_claims()
    assert len(claims) >= 3
    classes = {c["evidence_class"] for c in claims}
    assert "SPECULATIVE" in classes
    assert "ESTABLISHED" in classes


def test_add_and_filter():
    reg = EvidenceRegistry()
    c = reg.add_claim(
        statement="Test claim",
        evidence_class="HYPOTHESIS",
        domain="other",
        notes="unit test",
    )
    assert c.evidence_class == "HYPOTHESIS"
    filtered = reg.list_claims(evidence_class="HYPOTHESIS")
    assert any(x["claim_id"] == c.claim_id for x in filtered)


def test_invalid_class():
    reg = EvidenceRegistry()
    try:
        reg.add_claim("x", "NOT_A_CLASS", "other")
        assert False, "should have raised"
    except ValueError:
        pass
