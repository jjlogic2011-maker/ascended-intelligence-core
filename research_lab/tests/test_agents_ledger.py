"""Tests for evidence agents and ledger."""

from __future__ import annotations

from research_lab.agents.evidence.ledger import append_evidence, ledger_summary, read_ledger
from research_lab.agents.validation.claim_validator import validate_claim


def test_append_and_read_ledger():
    e = append_evidence(
        agent="TestAgent",
        action="unit_test",
        claim="ledger append works",
        classification="OPERATIONAL",
        evidence_type="log",
        status="verified",
    )
    assert e.entry_id
    assert e.entry_hash
    entries = read_ledger(limit=5)
    assert any(x["entry_id"] == e.entry_id for x in entries)


def test_consciousness_claim_downgraded():
    c = validate_claim(
        statement="Quantum mechanics proves consciousness",
        classification="ESTABLISHED",
        evidence_summary="none",
        working_functionality=False,
    )
    assert c.classification == "SPECULATIVE"


def test_ledger_summary_keys():
    s = ledger_summary()
    assert "total_entries" in s
    assert "tip_hash" in s
    assert "ledger_path" in s
