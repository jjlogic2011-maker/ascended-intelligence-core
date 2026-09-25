"""SHAPE — authorization state machine for TrustOS.

States: REQUESTED, ASSESSED, PENDING_HUMAN_APPROVAL, APPROVED, DENIED,
MODIFIED, ESCALATED, EXECUTED, REVOKED.

Every transition is validated against an explicit transition table.
Every transition produces an AuditEvent. Expired or revoked
authorizations cannot be executed.

This is a reference implementation, not a production authorization system.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class ShapeError(Exception):
    """Raised when a transition is illegal or execution is disallowed."""


class State(str, Enum):
    REQUESTED = "REQUESTED"
    ASSESSED = "ASSESSED"
    PENDING_HUMAN_APPROVAL = "PENDING_HUMAN_APPROVAL"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    MODIFIED = "MODIFIED"
    ESCALATED = "ESCALATED"
    EXECUTED = "EXECUTED"
    REVOKED = "REVOKED"


_TERMINAL = {State.DENIED, State.EXECUTED, State.REVOKED}

_TRANSITIONS = {
    State.REQUESTED: {State.ASSESSED, State.DENIED, State.ESCALATED},
    State.ASSESSED: {
        State.PENDING_HUMAN_APPROVAL,
        State.APPROVED,
        State.DENIED,
        State.ESCALATED,
    },
    State.PENDING_HUMAN_APPROVAL: {
        State.APPROVED,
        State.DENIED,
        State.MODIFIED,
        State.ESCALATED,
    },
    State.MODIFIED: {
        State.ASSESSED,
        State.PENDING_HUMAN_APPROVAL,
        State.DENIED,
    },
    State.ESCALATED: {State.ASSESSED, State.DENIED, State.REVOKED},
    State.APPROVED: {State.EXECUTED, State.REVOKED, State.MODIFIED},
    State.DENIED: set(),
    State.EXECUTED: set(),
    State.REVOKED: set(),
}


@dataclass
class AuditEvent:
    event_id: str
    timestamp: float
    from_state: State | None
    to_state: State
    actor: str
    reason: str | None = None

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "from_state": self.from_state.value if self.from_state else None,
            "to_state": self.to_state.value,
            "actor": self.actor,
            "reason": self.reason,
        }


@dataclass
class Authorization:
    request_id: str
    state: State = State.REQUESTED
    expires_at: float | None = None
    history: list = field(default_factory=list)

    def is_expired(self, now: float | None = None) -> bool:
        if self.expires_at is None:
            return False
        return (now if now is not None else time.time()) >= self.expires_at

    def can_execute(self, now: float | None = None) -> bool:
        if self.state == State.REVOKED:
            return False
        if self.is_expired(now):
            return False
        return self.state == State.APPROVED

    def transition(self, to_state, actor, reason=None):
        if self.state in _TERMINAL:
            raise ShapeError(
                f"cannot transition from terminal state {self.state.value}"
            )
        allowed = _TRANSITIONS.get(self.state, set())
        if to_state not in allowed:
            raise ShapeError(
                f"illegal transition {self.state.value} -> {to_state.value}"
            )
        if to_state == State.EXECUTED and not self.can_execute():
            raise ShapeError(
                "cannot EXECUTE: authorization is not APPROVED, "
                "or is expired, or is revoked"
            )
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            from_state=self.state,
            to_state=to_state,
            actor=actor,
            reason=reason,
        )
        self.state = to_state
        self.history.append(event)
        return event
