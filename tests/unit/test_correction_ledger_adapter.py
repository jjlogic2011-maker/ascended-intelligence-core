"""Tamper tests for the correction-to-ledger adapter."""

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
from security.ledger import LivingLedger


def build_graph():
    g = LineageGraph()
    g.add_edge("dataset", "modelA", material=True)
    g.add_edge("modelA", "agentC", material=True)
    return g


def closed_correction():
    r = CorrectionRegistry()
    c = r.register(build_graph(), "dataset", "label leakage", correction_id="corr-001")
    r.propagate(c.correction_id)
    for node in c.dispositions:
        r.set_disposition(c.correction_id, node, CorrectionState.REPAIRED)
    return c


def setup_env(tmp_path):
    ledger = LivingLedger()
    correction = closed_correction()
    envelope_dir = str(tmp_path / "envelopes")
    record_correction(
        ledger, correction,
        actor="test-actor", agent="test-agent", request_id="req-001",
        envelope_dir=envelope_dir,
    )
    return ledger, correction, envelope_dir


def test_clean_record_verifies(tmp_path):
    ledger, correction, envelope_dir = setup_env(tmp_path)
    result = verify_correction(ledger, correction.correction_id, envelope_dir)
    assert result["verified"] is True
    assert result["errors"] == []


def test_tampered_snapshot_hash_fails(tmp_path):
    ledger, correction, envelope_dir = setup_env(tmp_path)
    path = Path(envelope_dir) / f"{correction.correction_id}.json"
    rec = json.loads(path.read_text())
    rec["snapshot_sha256"] = "0" * 64
    path.write_text(json.dumps(rec))

    result = verify_correction(ledger, correction.correction_id, envelope_dir)
    assert result["verified"] is False
    assert "envelope_hash_mismatch" in result["errors"]


def test_tampered_disposition_fails(tmp_path):
    ledger, correction, envelope_dir = setup_env(tmp_path)
    path = Path(envelope_dir) / f"{correction.correction_id}.json"
    rec = json.loads(path.read_text())
    rec["dispositions"]["modelA"] = "EXEMPT"
    path.write_text(json.dumps(rec))

    result = verify_correction(ledger, correction.correction_id, envelope_dir)
    assert result["verified"] is False
    assert "envelope_hash_mismatch" in result["errors"]


def test_tampered_correction_id_breaks_link(tmp_path):
    ledger, correction, envelope_dir = setup_env(tmp_path)
    path = Path(envelope_dir) / f"{correction.correction_id}.json"
    rec = json.loads(path.read_text())
    rec["correction_id"] = "corr-DIFFERENT"
    path.write_text(json.dumps(rec))

    result = verify_correction(ledger, correction.correction_id, envelope_dir)
    assert result["verified"] is False
    assert "envelope_hash_mismatch" in result["errors"]


def test_deleted_envelope_is_detected(tmp_path):
    ledger, correction, envelope_dir = setup_env(tmp_path)
    path = Path(envelope_dir) / f"{correction.correction_id}.json"
    path.unlink()

    result = verify_correction(ledger, correction.correction_id, envelope_dir)
    assert result["verified"] is False
    assert "envelope_missing" in result["errors"]


def test_orphan_ledger_event_without_envelope(tmp_path):
    ledger, correction, envelope_dir = setup_env(tmp_path)
    path = Path(envelope_dir) / f"{correction.correction_id}.json"
    path.unlink()

    result = verify_correction(ledger, correction.correction_id, envelope_dir)
    assert result["ledger_event_present"] is True
    assert result["verified"] is False


def test_envelope_without_ledger_event(tmp_path):
    ledger = LivingLedger()
    correction = closed_correction()
    envelope_dir = str(tmp_path / "envelopes")

    Path(envelope_dir).mkdir(parents=True, exist_ok=True)
    path = Path(envelope_dir) / f"{correction.correction_id}.json"
    path.write_text(json.dumps(correction.to_record()))

    result = verify_correction(ledger, correction.correction_id, envelope_dir)
    assert result["envelope_present"] is True
    assert result["ledger_event_present"] is False
    assert result["verified"] is False
    assert "ledger_event_missing" in result["errors"]
