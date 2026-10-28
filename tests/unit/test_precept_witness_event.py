import pytest
from security.precept_witness_event import parse_precept_witness_event

def minimal(**overrides):
    data = {
        "event_id": "evt-1",
        "trace_id": "trace-1",
        "event_type": "evaluation",
        "timestamp": "2026-10-27T16:14:00Z",
        "actor": "nano-agent-1",
        "input_hash": "hash123"
    }
    data.update(overrides)
    return data

def test_minimal_valid():
    assert parse_precept_witness_event(minimal()) == minimal()

def test_full_valid():
    record = minimal(
        parent_event_id="evt-0",
        tool="tool-1",
        connector="conn-1",
        authority_request_id="auth-1",
        output_hash="hash456",
        claim_ids=["claim-1", "claim-2"],
        attributes={"score": 0.95}
    )
    assert parse_precept_witness_event(record) == record

def test_nullable_fields_valid():
    record = minimal(parent_event_id=None, output_hash=None)
    assert parse_precept_witness_event(record) == record

@pytest.mark.parametrize("field", ["event_id", "trace_id", "event_type", "timestamp", "actor", "input_hash"])
def test_missing_required(field):
    data = minimal()
    del data[field]
    with pytest.raises(ValueError, match="missing required"):
        parse_precept_witness_event(data)

def test_unknown_field_rejected():
    with pytest.raises(ValueError, match="unknown witness event fields"):
        parse_precept_witness_event(minimal(hallucinated=True))

def test_invalid_types():
    with pytest.raises(ValueError, match="must be an array of strings"):
        parse_precept_witness_event(minimal(claim_ids="not-a-list"))
    with pytest.raises(ValueError, match="must be an object"):
        parse_precept_witness_event(minimal(attributes="not-a-dict"))

def test_invalid_timestamp():
    with pytest.raises(ValueError, match="must be an RFC 3339"):
        parse_precept_witness_event(minimal(timestamp="not-a-date"))
