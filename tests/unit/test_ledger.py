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


def test_open_ledger_restart_preserves_chain(tmp_path):
    from security.ledger import open_ledger

    path = tmp_path / "durable.jsonl"
    l1 = open_ledger(str(path))
    e1 = l1.append(
        event_type="X", actor="a", agent="ag",
        request_id="r1", artifact_id="art",
    )
    e2 = l1.append(
        event_type="Y", actor="a", agent="ag",
        request_id="r2", artifact_id="art",
    )
    l2 = open_ledger(str(path))
    assert len(l2.events) == 2
    assert l2.events[0].event_hash == e1.event_hash
    assert l2.events[1].event_hash == e2.event_hash
    ok, errors = l2.verify()
    assert ok is True
    assert errors == []


def test_open_ledger_fails_closed_on_tamper(tmp_path):
    from security.ledger import LedgerError, open_ledger

    path = tmp_path / "tamper.jsonl"
    l = open_ledger(str(path))
    l.append(
        event_type="X", actor="a", agent="ag",
        request_id="r", artifact_id="art",
    )
    text = path.read_text(encoding="utf-8")
    data = json.loads(text.strip())
    data["artifact_id"] = "evil"
    path.write_text(json.dumps(data) + "\n", encoding="utf-8")
    try:
        open_ledger(str(path))
        raised = False
    except LedgerError:
        raised = True
    assert raised is True


def test_open_ledger_from_env_memory_by_default(monkeypatch):
    from security.ledger import open_ledger_from_env

    monkeypatch.delenv("AICI_LEDGER_PATH", raising=False)
    l = open_ledger_from_env()
    assert l._path is None


def test_schema_version_constant():
    from security.ledger import LEDGER_SCHEMA_VERSION

    assert LEDGER_SCHEMA_VERSION == 1
