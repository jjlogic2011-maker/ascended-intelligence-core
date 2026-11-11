"""Persistence tests for the correction-ledger adapter.

These prove that a correction recorded in one process can be verified
in a separate process after reloading from disk — the property that
makes the ledger useful for audit.
"""

import json
from pathlib import Path

from security.correction_ledger_adapter import (
    record_correction,
    verify_correction,
)
from security.correction_propagation import (
    CorrectionRegistry,
    CorrectionState,
    LineageGraph,
)
from security.ledger import LivingLedger, load_ledger


def build_graph():
    g = LineageGraph()
    g.add_edge("dataset", "modelA", material=True)
    g.add_edge("modelA", "agentC", material=True)
    return g


def closed_correction():
    r = CorrectionRegistry()
    c = r.register(build_graph(), "dataset", "label leakage", correction_id="corr-persist-001")
    r.propagate(c.correction_id)
    for node in c.dispositions:
        r.set_disposition(c.correction_id, node, CorrectionState.REPAIRED)
    return c


def test_correction_verifies_after_ledger_reload(tmp_path):
    """Record in one ledger instance, reload from disk, verify in the new instance."""
    ledger_path = str(tmp_path / "ledger.jsonl")
    envelope_dir = str(tmp_path / "envelopes")

    # Process 1: record
    ledger1 = LivingLedger(path=ledger_path)
    correction = closed_correction()
    record_correction(
        ledger1, correction,
        actor="actor", agent="agent", request_id="req-1",
        envelope_dir=envelope_dir,
    )
    assert ledger1.verify()[0] is True

    # Process 2: reload from disk
    ledger2 = load_ledger(ledger_path)
    assert len(ledger2.events) == 1
    assert ledger2.verify()[0] is True

    # Verify in the reloaded process
    result = verify_correction(ledger2, correction.correction_id, envelope_dir)
    assert result["verified"] is True
    assert result["errors"] == []


def test_reloaded_ledger_detects_envelope_deletion(tmp_path):
    """Even after reload, missing envelope fails verification."""
    ledger_path = str(tmp_path / "ledger.jsonl")
    envelope_dir = str(tmp_path / "envelopes")

    ledger1 = LivingLedger(path=ledger_path)
    correction = closed_correction()
    record_correction(
        ledger1, correction,
        actor="actor", agent="agent", request_id="req-1",
        envelope_dir=envelope_dir,
    )

    # Delete envelope, then reload ledger from disk
    (Path(envelope_dir) / f"{correction.correction_id}.json").unlink()
    ledger2 = load_ledger(ledger_path)

    result = verify_correction(ledger2, correction.correction_id, envelope_dir)
    assert result["verified"] is False
    assert "envelope_missing" in result["errors"]


def test_reloaded_ledger_detects_chain_tamper(tmp_path):
    """Hand-edit the JSONL file, reload, verify must fail."""
    ledger_path = str(tmp_path / "ledger.jsonl")
    envelope_dir = str(tmp_path / "envelopes")

    ledger1 = LivingLedger(path=ledger_path)
    correction = closed_correction()
    record_correction(
        ledger1, correction,
        actor="actor", agent="agent", request_id="req-1",
        envelope_dir=envelope_dir,
    )

    # Tamper with the on-disk JSONL
    lines = Path(ledger_path).read_text().strip().split("\n")
    data = json.loads(lines[0])
    data["artifact_id"] = "tampered-correction-id"
    Path(ledger_path).write_text(json.dumps(data) + "\n")

    ledger2 = load_ledger(ledger_path)
    ok, errors = ledger2.verify()
    assert ok is False
    assert any("event_hash" in e for e in errors)

    # And verification of the correction must also fail
    result = verify_correction(ledger2, correction.correction_id, envelope_dir)
    assert result["verified"] is False


def test_two_corrections_persist_in_order(tmp_path):
    """Two corrections recorded and reloaded preserve chain order."""
    ledger_path = str(tmp_path / "ledger.jsonl")
    envelope_dir = str(tmp_path / "envelopes")

    ledger1 = LivingLedger(path=ledger_path)

    r = CorrectionRegistry()
    c1 = r.register(build_graph(), "dataset", "first", correction_id="corr-a")
    r.propagate(c1.correction_id)
    for node in c1.dispositions:
        r.set_disposition(c1.correction_id, node, CorrectionState.REPAIRED)

    c2 = r.register(build_graph(), "dataset", "second", correction_id="corr-b")
    r.propagate(c2.correction_id)
    for node in c2.dispositions:
        r.set_disposition(c2.correction_id, node, CorrectionState.EXEMPT)

    record_correction(ledger1, c1, actor="a", agent="g", request_id="r1", envelope_dir=envelope_dir)
    record_correction(ledger1, c2, actor="a", agent="g", request_id="r2", envelope_dir=envelope_dir,
                      correction_of=ledger1.events[0].event_id)

    ledger2 = load_ledger(ledger_path)
    assert len(ledger2.events) == 2
    assert ledger2.verify()[0] is True
    assert ledger2.events[1].correction_of == ledger2.events[0].event_id

    assert verify_correction(ledger2, "corr-a", envelope_dir)["verified"] is True
    assert verify_correction(ledger2, "corr-b", envelope_dir)["verified"] is True
