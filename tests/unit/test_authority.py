import time

import pytest

from security.authority import (
    AuthorityError,
    GrantStore,
    issue_grant,
)


def test_issue_and_validate():
    g = issue_grant(
        principal_id="alice",
        agent_id="agent-1",
        scope={"read"},
    )
    assert g.is_valid()
    assert g.principal_id == "alice"
    assert g.agent_id == "agent-1"


def test_expired_grant_invalid():
    g = issue_grant(
        principal_id="alice",
        agent_id="agent-1",
        scope={"read"},
        expires_at=time.time() - 1,
    )
    assert g.is_valid() is False


def test_revoked_grant_invalid():
    g = issue_grant(
        principal_id="alice",
        agent_id="agent-1",
        scope={"read"},
    )
    g.revoke()
    assert g.is_valid() is False


def test_max_uses_enforced():
    g = issue_grant(
        principal_id="alice",
        agent_id="agent-1",
        scope={"read"},
        max_uses=2,
    )
    g.consume()
    g.consume()
    assert g.is_exhausted()
    assert g.is_valid() is False
    with pytest.raises(AuthorityError):
        g.consume()


def test_permits_scope():
    g = issue_grant(
        principal_id="alice",
        agent_id="agent-1",
        scope={"read", "write"},
    )
    assert g.permits("read") is True
    assert g.permits("write") is True
    assert g.permits("execute") is False
    assert g.permits("unknown-action") is False


def test_grant_store_add_and_get():
    store = GrantStore()
    g = issue_grant(principal_id="p", agent_id="a", scope={"read"})
    store.add(g)
    assert store.get(g.grant_id) is g


def test_grant_store_revoke():
    store = GrantStore()
    g = issue_grant(principal_id="p", agent_id="a", scope={"read"})
    store.add(g)
    store.revoke(g.grant_id)
    assert store.get(g.grant_id).revoked is True


def test_grant_store_unknown_revoke_raises():
    store = GrantStore()
    with pytest.raises(AuthorityError):
        store.revoke("nope")


def test_grant_distinct_ids():
    a = issue_grant(principal_id="p", agent_id="a", scope={"read"})
    b = issue_grant(principal_id="p", agent_id="a", scope={"read"})
    assert a.grant_id != b.grant_id


def test_used_count_starts_zero():
    g = issue_grant(principal_id="p", agent_id="a", scope={"read"})
    assert g.used_count == 0
