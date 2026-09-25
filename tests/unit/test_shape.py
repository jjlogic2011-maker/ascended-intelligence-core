import time

import pytest

from security.shape import Authorization, ShapeError, State


def _approved():
    a = Authorization(request_id="r")
    a.transition(State.ASSESSED, actor="system")
    a.transition(State.APPROVED, actor="human")
    return a


def test_illegal_transition_rejected():
    a = Authorization(request_id="r")
    with pytest.raises(ShapeError):
        a.transition(State.EXECUTED, actor="system")


def test_happy_path_execution():
    a = _approved()
    ev = a.transition(State.EXECUTED, actor="system")
    assert a.state == State.EXECUTED
    assert ev.from_state == State.APPROVED
    assert ev.to_state == State.EXECUTED


def test_expired_cannot_execute():
    a = _approved()
    a.expires_at = time.time() - 1
    with pytest.raises(ShapeError):
        a.transition(State.EXECUTED, actor="system")


def test_revoked_cannot_execute():
    a = _approved()
    a.transition(State.REVOKED, actor="human")
    with pytest.raises(ShapeError):
        a.transition(State.EXECUTED, actor="system")


def test_terminal_state_is_terminal():
    a = _approved()
    a.transition(State.REVOKED, actor="human")
    with pytest.raises(ShapeError):
        a.transition(State.APPROVED, actor="human")


def test_transitions_are_audited():
    a = _approved()
    assert len(a.history) == 2
    assert a.history[0].to_state == State.ASSESSED
    assert a.history[1].to_state == State.APPROVED


def test_can_execute_predicate():
    a = _approved()
    assert a.can_execute() is True
    a.expires_at = time.time() - 1
    assert a.can_execute() is False
