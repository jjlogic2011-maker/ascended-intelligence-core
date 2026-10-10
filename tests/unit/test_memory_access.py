import time

import pytest

from security.ledger import LivingLedger
from security.memory_access import (
    MemoryAccessRecorder,
    schedule_forgetting,
    should_promote_memory,
    stable_hash,
)


def test_stable_hash_deterministic():
    a = stable_hash({"b": 2, "a": 1})
    b = stable_hash({"a": 1, "b": 2})
    assert a == b
    assert len(a) == 64


def test_stable_hash_changes_on_content():
    assert stable_hash({"x": 1}) != stable_hash({"x": 2})


def test_record_retrieval_creates_receipt():
    recorder = MemoryAccessRecorder()
    receipt = recorder.record_retrieval(
        principal_id="alice",
        agent_id="agent-1",
        memory_ids=["mem-a", "mem-b"],
        query_hash=stable_hash({"q": "test"}),
        purpose="planning",
    )
    assert receipt.retrieval_id in recorder.retrievals
    assert receipt.memory_ids == ["mem-a", "mem-b"]
    assert receipt.principal_id == "alice"


def test_record_retrieval_requires_fields():
    recorder = MemoryAccessRecorder()
    with pytest.raises(ValueError):
        recorder.record_retrieval(
            principal_id="",
            agent_id="agent-1",
            memory_ids=["mem-a"],
            query_hash="x",
            purpose="planning",
        )
    with pytest.raises(ValueError):
        recorder.record_retrieval(
            principal_id="alice",
            agent_id="agent-1",
            memory_ids=[],
            query_hash="x",
            purpose="planning",
        )


def test_record_retrieval_writes_ledger():
    ledger = LivingLedger()
    recorder = MemoryAccessRecorder(ledger=ledger)
    recorder.record_retrieval(
        principal_id="alice",
        agent_id="agent-1",
        memory_ids=["mem-a"],
        query_hash="q",
        purpose="planning",
    )
    assert len(ledger.events) == 1
    assert ledger.events[0].event_type == "MEMORY_RETRIEVED"
    ok, errors = ledger.verify()
    assert ok, errors


def test_link_action_to_retrieval():
    ledger = LivingLedger()
    recorder = MemoryAccessRecorder(ledger=ledger)
    receipt = recorder.record_retrieval(
        principal_id="alice",
        agent_id="agent-1",
        memory_ids=["mem-a"],
        query_hash="q",
        purpose="planning",
    )
    link = recorder.link_action_to_retrieval(
        action_receipt_id="action-1",
        retrieval_id=receipt.retrieval_id,
    )
    assert link.action_receipt_id == "action-1"
    assert len(ledger.events) == 2
    assert ledger.events[-1].event_type == "MEMORY_USED_FOR_ACTION"


def test_link_requires_known_retrieval():
    recorder = MemoryAccessRecorder()
    with pytest.raises(ValueError):
        recorder.link_action_to_retrieval(
            action_receipt_id="action-1",
            retrieval_id="unknown",
        )


def test_promotion_requires_human_approval_for_high_risk():
    d = should_promote_memory(
        memory_id="m1",
        novelty_score=0.9,
        contradiction_score=0.9,
        use_count=10,
        risk_tier="high",
        human_approved=False,
    )
    assert d.promote is False
    assert d.reason == "high_risk_requires_human_approval"


def test_promotion_by_contradiction():
    d = should_promote_memory(
        memory_id="m1",
        novelty_score=0.1,
        contradiction_score=0.8,
        use_count=0,
        risk_tier="low",
        human_approved=False,
    )
    assert d.promote is True
    assert d.reason == "contradiction_or_prediction_error"


def test_promotion_rejects_insignificant():
    d = should_promote_memory(
        memory_id="m1",
        novelty_score=0.1,
        contradiction_score=0.1,
        use_count=1,
        risk_tier="low",
        human_approved=False,
    )
    assert d.promote is False
    assert d.reason == "insufficient_significance"


def test_forgetting_legal_hold_wins():
    d = schedule_forgetting(
        memory_id="m1",
        retention_class="session",
        last_retrieved_at=0,
        dispute_status="legal_hold",
    )
    assert d.decision == "legal_hold"


def test_forgetting_archives_stale_session():
    now = time.time()
    d = schedule_forgetting(
        memory_id="m1",
        retention_class="session",
        last_retrieved_at=now - 60 * 60 * 24 * 60,
        dispute_status="active",
        now=now,
    )
    assert d.decision == "archive"


def test_forgetting_keeps_enterprise():
    d = schedule_forgetting(
        memory_id="m1",
        retention_class="enterprise",
        last_retrieved_at=0,
        dispute_status="active",
    )
    assert d.decision == "keep"
