import time

from security.governance import (
    AgentIdentity,
    GovernanceEngine,
    GovernanceRequest,
)
from security.ledger import LivingLedger
from security.shape import Authorization, State


def _engine():
    ledger = LivingLedger()
    agents = {
        "agent-ok": AgentIdentity("agent-ok", frozenset({"read", "write"})),
        "agent-narrow": AgentIdentity("agent-narrow", frozenset({"read"})),
        "agent-revoked": AgentIdentity(
            "agent-revoked", frozenset({"read", "write"}), revoked=True
        ),
    }
    policies = {"read": {"read"}, "write": {"write"}}
    return GovernanceEngine(ledger=ledger, agents=agents, policies=policies), ledger


def _approved():
    a = Authorization(request_id="r")
    a.transition(State.ASSESSED, actor="system")
    a.transition(State.APPROVED, actor="human")
    return a


def _request(agent_id="agent-ok", action="write", request_id="r-1"):
    return GovernanceRequest(
        request_id=request_id,
        agent_id=agent_id,
        action=action,
        artifact_id="art-1",
        artifact_content=b"data",
        creator="creator-1",
        version="1.0.0",
        provenance={"source": "test"},
    )


def test_happy_path_executes_and_records():
    engine, ledger = _engine()
    result = engine.process(_request(), authorization=_approved())
    assert result.executed is True
    assert result.receipt_event_id is not None
    assert result.fingerprint is not None
    ok, errors = ledger.verify()
    assert ok, errors


def test_denied_when_not_approved():
    engine, _ = _engine()
    auth = Authorization(request_id="r")
    result = engine.process(_request(), authorization=auth)
    assert result.executed is False
    assert result.decision == "DENIED"


def test_denied_when_expired():
    engine, _ = _engine()
    auth = _approved()
    auth.expires_at = time.time() - 1
    result = engine.process(_request(), authorization=auth)
    assert result.executed is False
    assert "expired" in result.reason


def test_unknown_agent_denied():
    engine, _ = _engine()
    result = engine.process(
        _request(agent_id="ghost"), authorization=_approved()
    )
    assert result.executed is False


def test_revoked_agent_denied():
    engine, _ = _engine()
    result = engine.process(
        _request(agent_id="agent-revoked"), authorization=_approved()
    )
    assert result.executed is False


def test_authority_escalation_denied():
    engine, _ = _engine()
    result = engine.process(
        _request(agent_id="agent-narrow", action="write"),
        authorization=_approved(),
    )
    assert result.executed is False
    assert "authority" in result.reason


def test_revoked_authorization_denied():
    engine, _ = _engine()
    auth = _approved()
    auth.transition(State.REVOKED, actor="human")
    result = engine.process(_request(), authorization=auth)
    assert result.executed is False
    assert result.decision == "REVOKED"


def test_replayed_request_denied():
    engine, _ = _engine()
    auth = _approved()
    first = engine.process(_request(), authorization=auth)
    second = engine.process(_request(), authorization=auth)
    assert first.executed is True
    assert second.executed is False
    assert "replayed" in second.reason


def test_no_policy_denied():
    engine, _ = _engine()
    engine.policies = {}
    result = engine.process(_request(action="write"), authorization=_approved())
    assert result.executed is False
    assert "no policy" in result.reason


def test_evidence_contains_fingerprint_and_receipt():
    engine, _ = _engine()
    result = engine.process(_request(), authorization=_approved())
    assert "fingerprint" in result.evidence
    assert "receipt_event_id" in result.evidence
    assert len(result.evidence["fingerprint"]) == 64
