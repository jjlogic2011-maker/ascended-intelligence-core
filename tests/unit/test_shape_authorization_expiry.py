"""Focused regression tests for direct SHAPE authorization expiry and revocation."""
import pytest

from security.shape import Authorization, ShapeError, State


def approved_authorization(*, expires_at=None):
    auth = Authorization(request_id="audit-state", expires_at=expires_at)
    auth.transition(State.ASSESSED, actor="system")
    auth.transition(State.APPROVED, actor="human")
    return auth


def test_expired_approval_cannot_execute(monkeypatch):
    auth = approved_authorization(expires_at=101)
    monkeypatch.setattr("security.shape.time.time", lambda: 101)

    assert not auth.can_execute()
    with pytest.raises(ShapeError, match="cannot EXECUTE"):
        auth.transition(State.EXECUTED, actor="agent")


def test_revoked_approval_cannot_execute():
    auth = approved_authorization()
    auth.transition(State.REVOKED, actor="human")

    assert not auth.can_execute()
    with pytest.raises(ShapeError, match="terminal state REVOKED"):
        auth.transition(State.EXECUTED, actor="agent")
