import json
import os
import tempfile

from security.ledger import (
    GENESIS,
    LedgerEvent,
    LivingLedger,
    load_ledger,
)


def test_first_event_links_to_genesis():
    l = LivingLedger()
    ev = l.append(
        event_type="X", actor="a", agent="ag",
        request_id="r", artifact_id="art",
    )
    assert ev.previous_event_hash == GENESIS


def test_chain_links_correctly():
    l = LivingLedger()
    e1 = l.append(
        event_type="X", actor="a", agent="ag",
        request_id="r", artifact_id="art",
    )
    e2 = l.append(
        event_type="Y", actor="a", agent="ag",
        request_id="r", artifact_id="art",
    )
    assert e2.previous_event_hash == e1.event_hash


def test_verify_ok():
    l = LivingLedger()
    l.append(
        event_type="X", actor="a", agent="ag",
        request_id="r", artifact_id="art",
    )
    ok, errors = l.verify()
    assert ok is True
    assert errors == []


def test_verify_detects_tamper_on_disk():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "ledger.jsonl")
        l = LivingLedger(path=path)
        l.append(
            event_type="X", actor="a", agent="ag",
            request_id="r", artifact_id="art",
        )
        with open(path, "r", encoding="utf-8") as fh:
            data = json.loads(fh.readline())
        data["artifact_id"] = "tampered"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(data) + "\n")
        loaded = load_ledger(path)
        ok, errors = loaded.verify()
        assert ok is False
        assert any("event_hash" in e for e in errors)


def test_verify_detects_broken_link():
    l = LivingLedger()
    l.append(
        event_type="X", actor="a", agent="ag",
        request_id="r", artifact_id="art",
    )
    l.append(
        event_type="Y", actor="a", agent="ag",
        request_id="r", artifact_id="art",
    )
    tampered = dict(l._events[1].to_dict())
    tampered["previous_event_hash"] = "0" * 63 + "1"
    l._events[1] = LedgerEvent(**tampered)
    ok, errors = l.verify()
    assert ok is False
    assert any("previous_event_hash" in e for e in errors)


def test_event_contains_required_fields():
    l = LivingLedger()
    ev = l.append(
        event_type="X", actor="a", agent="ag",
        request_id="r", artifact_id="art",
    )
    d = ev.to_dict()
    for field in (
        "event_id", "correlation_id", "timestamp", "event_type",
        "actor", "agent", "request_id", "artifact_id",
        "correction_of", "previous_event_hash", "event_hash",
    ):
        assert field in d


def test_correction_of_field():
    l = LivingLedger()
    original = l.append(
        event_type="X", actor="a", agent="ag",
        request_id="r", artifact_id="art",
    )
    correction = l.append(
        event_type="CORRECTION", actor="a", agent="ag",
        request_id="r", artifact_id="art",
        correction_of=original.event_id,
    )
    assert correction.correction_of == original.event_id

