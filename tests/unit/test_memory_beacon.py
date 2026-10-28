import pytest
from security.memory_beacon import parse_memory_beacon

def minimal(**overrides):
    data = {
        "beacon_id": "b-001",
        "timestamp": "2026-10-27T16:14:00Z",
        "emotional_tone": "focused",
        "difficulty_burden": "high",
        "outcome": "success",
        "lesson_learned": "Strict schema validation prevents drift.",
        "confidence": "ledgered"
    }
    data.update(overrides)
    return data

def test_minimal_valid():
    assert parse_memory_beacon(minimal()) == minimal()

def test_full_valid():
    record = minimal(
        future_recall_cues=["drift", "schema", "strict"],
        cross_ledger_link="ledger://tx-123"
    )
    assert parse_memory_beacon(record) == record

@pytest.mark.parametrize("field", [
    "beacon_id", "timestamp", "emotional_tone", 
    "difficulty_burden", "outcome", "lesson_learned", "confidence"
])
def test_missing_required(field):
    data = minimal()
    del data[field]
    with pytest.raises(ValueError, match="missing required"):
        parse_memory_beacon(data)

def test_unknown_field_rejected():
    with pytest.raises(ValueError, match="unknown MemoryBeacon fields"):
        parse_memory_beacon(minimal(hallucinated=True))

def test_invalid_confidence():
    with pytest.raises(ValueError, match="confidence must be one of"):
        parse_memory_beacon(minimal(confidence="unknown"))
    with pytest.raises(ValueError, match="confidence must be one of"):
        parse_memory_beacon(minimal(confidence="VERIFIED"))

def test_invalid_recall_cues():
    with pytest.raises(ValueError, match="must be an array"):
        parse_memory_beacon(minimal(future_recall_cues="not-a-list"))
    with pytest.raises(ValueError, match="items must be strings"):
        parse_memory_beacon(minimal(future_recall_cues=[123, 456]))

def test_invalid_timestamp():
    with pytest.raises(ValueError, match="must be an RFC 3339"):
        parse_memory_beacon(minimal(timestamp="not-a-date"))
