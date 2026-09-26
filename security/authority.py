"""Authority grants — first-class delegated authority for agents.

A grant binds:
    principal_id (human) -> agent_id (agent) with a scope, expiry,
    revocation state, and optional use limit.

Grants are not identity. A grant is a record that a principal
authorized an agent to perform scoped actions until a condition
expires or a revocation occurs.

This is a reference implementation. It does not implement
cryptographic signing, distributed storage, or key rotation.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass


class AuthorityError(Exception):
    """Raised when a grant is invalid, expired, revoked, or exhausted."""


@dataclass
class AuthorityGrant:
    grant_id: str
    principal_id: str
    agent_id: str
    scope: frozenset
    issued_at: float
    expires_at: float | None = None
    revoked: bool = False
    max_uses: int | None = None
    used_count: int = 0

    def is_expired(self, now: float | None = None) -> bool:
        if self.expires_at is None:
            return False
        return (now if now is not None else time.time()) >= self.expires_at

    def is_exhausted(self) -> bool:
        if self.max_uses is None:
            return False
        return self.used_count >= self.max_uses

    def is_valid(self, now: float | None = None) -> bool:
        if self.revoked:
            return False
        if self.is_expired(now):
            return False
        if self.is_exhausted():
            return False
        return True

    def permits(self, action: str) -> bool:
        required = self._required_scope(action)
        return required.issubset(self.scope) if required else False

    @staticmethod
    def _required_scope(action: str) -> frozenset:
        mapping = {
            "read": frozenset({"read"}),
            "write": frozenset({"write"}),
            "execute": frozenset({"execute"}),
            "external-tool": frozenset({"external"}),
        }
        return mapping.get(action, frozenset())

    def consume(self) -> None:
        if not self.is_valid():
            raise AuthorityError("cannot consume invalid grant")
        self.used_count += 1

    def revoke(self) -> None:
        self.revoked = True


def issue_grant(
    *,
    principal_id: str,
    agent_id: str,
    scope: set,
    expires_at: float | None = None,
    max_uses: int | None = None,
) -> AuthorityGrant:
    return AuthorityGrant(
        grant_id=str(uuid.uuid4()),
        principal_id=principal_id,
        agent_id=agent_id,
        scope=frozenset(scope),
        issued_at=time.time(),
        expires_at=expires_at,
        max_uses=max_uses,
    )


class GrantStore:
    """In-memory grant store. Single-writer, no persistence."""

    def __init__(self):
        self._grants: dict = {}

    def add(self, grant: AuthorityGrant) -> None:
        self._grants[grant.grant_id] = grant

    def get(self, grant_id: str) -> AuthorityGrant | None:
        return self._grants.get(grant_id)

    def revoke(self, grant_id: str) -> None:
        g = self._grants.get(grant_id)
        if g is None:
            raise AuthorityError(f"unknown grant: {grant_id}")
        g.revoke()

    def all_grants(self) -> list:
        return list(self._grants.values())
