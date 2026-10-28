import pytest
from security.claim_record import parse_claim_record

def minimal(**overrides):
    data = {"claim_id": "c-001", "claim_text": "The sky is blue.", "status": "observed", "confidence": 0.95}
    data.update(overrides)
    return data

def test_minimal_record():
    assert parse_claim_record(minimal()) == minimal()

def test_full_record_with_evidence():
    record = minimal(source="Direct observation", evidence=[{"type": "image", "url": "example.com/sky.jpg"}], review_date="2026-10-27", public_safe_wording="The sky appears blue.", status="verified", confidence=1.0)
    assert parse_claim_record(record) == record

@pytest.mark.parametrize("field", ["claim_id", "claim_text", "status", "confidence"])
def test_missing_required_rejected(field):
    data = minimal(); del data[field]
    with pytest.raises(ValueError, match="missing required"): parse_claim_record(data)

@pytest.mark.parametrize("bad_status", ["unknown", "APPROVED", "false", 123])
def test_invalid_status_rejected(bad_status):
    with pytest.raises(ValueError, match="status must be one of"): parse_claim_record(minimal(status=bad_status))

@pytest.mark.parametrize("bad_conf", [-0.1, 1.1, "high", None, True])
def test_invalid_confidence_rejected(bad_conf):
    with pytest.raises(ValueError, match="confidence must be"): parse_claim_record(minimal(confidence=bad_conf))

def test_invalid_evidence_rejected():
    with pytest.raises(ValueError, match="evidence must be"): parse_claim_record(minimal(evidence="not a list"))
    with pytest.raises(ValueError, match="evidence must be"): parse_claim_record(minimal(evidence=["string not dict"]))

def test_unknown_field_rejected():
    with pytest.raises(ValueError, match="unknown ClaimRecord fields"): parse_claim_record(minimal(hallucinated_field=True))
