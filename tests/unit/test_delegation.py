import pytest
from security.authority import AuthorityError, issue_grant
from security.delegation import delegate

@pytest.fixture
def parent():
    return issue_grant(principal_id="alice", agent_id="agent-a", scope={"read", "write"}, max_uses=10)

def test_valid_delegation(parent):
    child = delegate(parent, new_agent_id="agent-b", requested_scope={"read"})
    assert child.scope == {"read"}
    assert child.parent_grant_id == parent.grant_id

def test_cannot_expand_scope(parent):
    with pytest.raises(AuthorityError):
        delegate(parent, new_agent_id="agent-b", requested_scope={"read", "execute"})
