"""TrustOS capability delegation."""
from __future__ import annotations
import time
import uuid
from dataclasses import dataclass
from security.authority import AuthorityGrant, AuthorityError

@dataclass
class DelegatedGrant(AuthorityGrant):
    parent_grant_id: str | None = None
    depth: int = 0

MAX_DELEGATION_DEPTH = 3

def delegate(parent: AuthorityGrant, *, new_agent_id: str, requested_scope: set, expires_at: float | None = None, max_uses: int | None = None) -> DelegatedGrant:
    if not parent.is_valid():
        raise AuthorityError("parent grant is invalid")
    if not set(requested_scope).issubset(parent.scope):
        raise AuthorityError("requested scope exceeds parent")
    now = time.time()
    if expires_at is not None:
        parent_exp = parent.expires_at if parent.expires_at is not None else float("inf")
        if expires_at > parent_exp:
            raise AuthorityError("cannot outlive parent")
    if max_uses is not None and parent.max_uses is not None:
        if max_uses > (parent.max_uses - parent.used_count):
            raise AuthorityError("max_uses exceeds parent remaining")
    if getattr(parent, "depth", 0) >= MAX_DELEGATION_DEPTH:
        raise AuthorityError("depth limit reached")
    return DelegatedGrant(
        grant_id=str(uuid.uuid4()), principal_id=parent.principal_id,
        agent_id=new_agent_id, scope=frozenset(requested_scope), issued_at=now,
        expires_at=expires_at if expires_at is not None else parent.expires_at,
        max_uses=max_uses, parent_grant_id=parent.grant_id, depth=getattr(parent, "depth", 0) + 1
    )
