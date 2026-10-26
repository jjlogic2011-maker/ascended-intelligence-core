import time
import pytest
from security.shape import Authorization, ShapeError, State

def test_expired_approval_cannot_execute():
    auth = Authorization(request_id="req-1")
    auth.transition(State.ASSESSED, actor="system")
    auth.transition(State.APPROVED, actor="human")
    auth.expires_at = time.time() - 10
    with pytest.raises(ShapeError):
        auth.transition(State.EXECUTED, actor="system")

def test_revoked_approval_cannot_execute():
    auth = Authorization(request_id="req-1")
    auth.transition(State.ASSESSED, actor="system")
    auth.transition(State.APPROVED, actor="human")
    auth.transition(State.REVOKED, actor="human")
    with pytest.raises(ShapeError):
        auth.transition(State.EXECUTED, actor="system")
