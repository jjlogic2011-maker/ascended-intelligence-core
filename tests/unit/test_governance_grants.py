import time

from security.authority import issue_grant
from security.governance import (
    AgentIdentity,
    GovernanceEngine,
    GovernanceRequest,
    process_with_grant,
)
from security.ledger import LivingLedger


def _engine():
    ledger = LivingLedger()
    agents = {
        "agent-ok": AgentIdentity("agent-ok", frozenset({"read", "write"})),
    }
    policies = {"read": {"read"}, "write": {"write"}}
    return GovernanceEngine(ledger=ledger, agents=agents, policies=policies), ledger


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


def test_valid_grant_permits_execution():
    engine, ledger = _engine()
    grant = issue_grant(
        principal_id="alice", agent_id="agent-ok", scope={"read", "write"}
    )
    result = process_with_grant(engine, _request(), grant=grant)
    assert result.executed is True
    assert grant.used_count == 1
    ok, _ = ledger.verify()
    assert ok


def test_expired_grant_blocks():
    engine, _ = _engine()
    grant = issue_grant(
        principal_id="alice", agent_id="agent-ok",
        scope={"read", "write"}, expires_at=time.time() - 1,
    )
    result = process_with_grant(engine, _request(), grant=grant)
    assert result.executed is False
    assert "expired" in result.reason
    assert grant.used_count == 0


def test_revoked_grant_blocks():
    engine, _ = _engine()
    grant = issue_grant(
        principal_id="alice", agent_id="agent-ok", scope={"read", "write"}
    )
    grant.revoke()
    result = process_with_grant(engine, _request(), grant=grant)
    assert result.executed is False


def test_wrong_agent_blocks():
    engine, _ = _engine()
    grant = issue_grant(
        principal_id="alice", agent_id="agent-different", scope={"read", "write"}
    )
    result = process_with_grant(engine, _request(agent_id="agent-ok"), grant=grant)
    assert result.executed is False
    assert "does not match" in result.reason


def test_insufficient_scope_blocks():
    engine, _ = _engine()
    grant = issue_grant(
        principal_id="alice", agent_id="agent-ok", scope={"read"}
    )
    result = process_with_grant(engine, _request(action="write"), grant=grant)
    assert result.executed is False
    assert "scope" in result.reason


def test_max_uses_decrements_on_success():
    engine, _ = _engine()
    grant = issue_grant(
        principal_id="alice", agent_id="agent-ok",
        scope={"read", "write"}, max_uses=2,
    )
    r1 = process_with_grant(engine, _request(request_id="r-1"), grant=grant)
    r2 = process_with_grant(engine, _request(request_id="r-2"), grant=grant)
    r3 = process_with_grant(engine, _request(request_id="r-3"), grant=grant)
    assert r1.executed is True
    assert r2.executed is True
    assert r3.executed is False
    assert grant.used_count == 2
