from concurrent.futures import ThreadPoolExecutor
import pytest
from security.approval_service import ApprovalService
from security.human_gates import enforce_human_gate
from security.shape import Authorization, ShapeError, State


@pytest.fixture
def setup(tmp_path):
    now = [100.0]
    def verify(credential, action, resource):
        return "human" if credential == "verified-session" else None
    service = ApprovalService(tmp_path / "approvals.db", verify_human=verify, clock=lambda: now[0])
    scope = dict(request_id="r1", requester_id="agent", action="production-deploy",
                 resource="staging", arguments={"commit": "abc"})
    return service, scope, now


def test_approved_transaction_and_replay(setup):
    service, scope, _ = setup
    approval = service.issue(credential="verified-session", **scope)
    auth = Authorization("r1")
    for state in (State.ASSESSED, State.PENDING_HUMAN_APPROVAL, State.APPROVED):
        auth.transition(state, actor="human")
    assert enforce_human_gate(auth, scope["action"], service=service, approval_id=approval,
                              requester_id="agent", resource="staging", arguments=scope["arguments"]) == "human"
    with pytest.raises(ShapeError):
        service.consume(approval, **scope)


@pytest.mark.parametrize("change", ["resource", "arguments", "request_id", "requester_id", "action"])
def test_scope_change_rejected(setup, change):
    service, scope, _ = setup
    approval = service.issue(credential="verified-session", **scope)
    changed = dict(scope, **{change: {} if change == "arguments" else "different"})
    with pytest.raises(ShapeError):
        service.consume(approval, **changed)
    service.consume(approval, **scope)


def test_expiry_revocation_and_unverified_human(setup):
    service, scope, now = setup
    with pytest.raises(ShapeError):
        service.issue(credential="forged", **scope)
    with pytest.raises(ShapeError):
        service.issue(credential="verified-session", **dict(scope, requester_id="human"))
    approval = service.issue(credential="verified-session", ttl=1, **scope)
    now[0] = 101
    with pytest.raises(ShapeError):
        service.consume(approval, **scope)
    approval = service.issue(credential="verified-session", **scope)
    service.revoke(approval)
    with pytest.raises(ShapeError):
        service.consume(approval, **scope)


def test_concurrent_consumption_and_restart(setup):
    service, scope, _ = setup
    approval = service.issue(credential="verified-session", **scope)
    other = ApprovalService(service.path, verify_human=service.verify_human, clock=service.clock)
    def attempt(_):
        try:
            other.consume(approval, **scope)
            return 1
        except ShapeError:
            return 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(8))) == 1


@pytest.mark.parametrize("state", [State.REQUESTED, State.PENDING_HUMAN_APPROVAL, State.DENIED, State.REVOKED])
def test_nonapproved_fails_closed(state):
    with pytest.raises(ShapeError):
        enforce_human_gate(Authorization("r1", state=state), "production-deploy")


def test_history_without_service_is_not_approval():
    auth = Authorization("r1")
    for state in (State.ASSESSED, State.PENDING_HUMAN_APPROVAL, State.APPROVED):
        auth.transition(state, actor="agent")
    with pytest.raises(ShapeError):
        enforce_human_gate(auth, "production-deploy")


def test_governance_approval_to_verified_receipt(setup):
    from security.governance import AgentIdentity, GovernanceEngine, GovernanceRequest
    from security.ledger import LivingLedger
    service, scope, _ = setup
    ledger = LivingLedger()
    engine = GovernanceEngine(ledger=ledger,
        agents={"agent": AgentIdentity("agent", frozenset({"deploy"}))},
        policies={"production-deploy": {"deploy"}})
    request = GovernanceRequest("r1", "agent", "production-deploy", "staging",
                                b"abc", "human", "0.2", {})
    auth = Authorization("r1")
    for state in (State.ASSESSED, State.PENDING_HUMAN_APPROVAL, State.APPROVED):
        auth.transition(state, actor="human")
    assert not engine.process(request, authorization=auth).executed
    approval = service.issue(credential="verified-session", **scope)
    result = engine.process(request, authorization=auth, approval_service=service,
                            approval_id=approval, arguments=scope["arguments"])
    assert result.executed and result.receipt_event_id
    assert ledger.verify()[0]
    assert not engine.process(request, authorization=auth, approval_service=service,
                              approval_id=approval, arguments=scope["arguments"]).executed
