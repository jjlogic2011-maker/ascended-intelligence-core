import pytest

from security.memory_beacon import parse_memory_beacon


def minimal(**overrides):
    data = {
        "beacon_id": "b-001",
        "date": "2026-10-28",
        "mission": "Schema reconciliation",
        "outcome": "success",
        "confidence": "ledgered",
    }
    data.update(overrides)
    return data


def test_minimal_valid():
    assert parse_memory_beacon(minimal()) == minimal()


def test_full_valid_including_schema_optionals():
    record = minimal(
        participants=["reviewer", "operator"],
        emotional_tone="focused",
        difficulty_burden="moderate",
        lesson_learned="align parser and schema",
        future_recall_cues=["drift", "schema"],
        cross_ledger_link="ledger://tx-123",
    )
    assert parse_memory_beacon(record) == record


@pytest.mark.parametrize(
    "field",
    ["beacon_id", "date", "mission", "outcome", "confidence"],
)
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


def test_invalid_recall_cues():
    with pytest.raises(ValueError, match="must be an array"):
        parse_memory_beacon(minimal(future_recall_cues="not-a-list"))


def test_invalid_participants():
    with pytest.raises(ValueError, match="must be an array"):
        parse_memory_beacon(minimal(participants="alice"))


def test_invalid_date():
    with pytest.raises(ValueError, match="must be a YYYY-MM-DD"):
        parse_memory_beacon(minimal(date="2026/10/28"))
