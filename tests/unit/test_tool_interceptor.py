"""Unit tests for TrustOS Integration Interceptor v2."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from security.integration.interceptor import (
    ToolRequest,
    build_default_interceptor,
    classify_tool,
    is_consequential,
    preview_policy,
)


def test_classify_non_consequential():
    assert classify_tool("search") == "execute"
    assert not is_consequential("search")


def test_classify_consequential():
    assert is_consequential("production_deploy")
    assert is_consequential("deploy")


def test_preview_policy():
    p = preview_policy("deploy")
    assert p["consequential"] is True
    assert p["requires_human_approval"] is True
    p2 = preview_policy("search")
    assert p2["auto_executable"] is True


def test_non_consequential_auto_executes():
    ix = build_default_interceptor()
    r = ix.handle(ToolRequest(tool_name="search", arguments={"q": "t"}, agent_id="model-agent"))
    assert r.executed is True
    assert r.consequential is False
    assert r.receipt_event_id is not None
    assert r.compact and r.compact.startswith("[OK]")


def test_consequential_pending():
    ix = build_default_interceptor()
    r = ix.handle(ToolRequest(
        tool_name="production_deploy",
        arguments={"env": "prod"},
        agent_id="model-agent",
    ))
    assert r.executed is False
    assert r.decision == "PENDING_HUMAN_APPROVAL"
    assert r.pending_id
    assert r.compact.startswith("[GATE]")
    assert len(ix.list_pending()) == 1


def test_deny_pending():
    ix = build_default_interceptor()
    r = ix.handle(ToolRequest(
        tool_name="destructive_edit",
        arguments={"path": "/x"},
        agent_id="model-agent",
    ))
    denied = ix.resolve_pending(r.pending_id, approve=False, deny_reason="unsafe path")
    assert denied.executed is False
    assert denied.decision == "DENIED"
    assert "unsafe" in denied.reason
    assert ix.list_pending() == []


def test_idempotency():
    ix = build_default_interceptor()
    tr = ToolRequest(
        tool_name="search",
        arguments={"q": "idem"},
        agent_id="model-agent",
        client_request_id="client-abc-1",
    )
    a = ix.handle(tr)
    b = ix.handle(tr)
    assert a.request_id == b.request_id
    assert a.receipt_event_id == b.receipt_event_id


def test_model_trail():
    ix = build_default_interceptor()
    mid = "model-turn-42"
    ix.handle(ToolRequest(tool_name="search", arguments={}, agent_id="model-agent", model_request_id=mid))
    ix.handle(ToolRequest(tool_name="search", arguments={"q": "2"}, agent_id="model-agent", model_request_id=mid))
    trail = ix.trail_by_model(mid)
    assert len(trail) == 2


def test_batch_preview():
    ix = build_default_interceptor()
    previews = ix.batch_preview(["search", "deploy", "read_file"])
    assert len(previews) == 3
    assert previews[1]["consequential"] is True


def test_ledger_integrity():
    from security.ledger import LivingLedger
    ledger = LivingLedger()
    ix = build_default_interceptor(ledger=ledger)
    ix.handle(ToolRequest(tool_name="search", arguments={}, agent_id="model-agent"))
    ok, errors = ledger.verify()
    assert ok, errors
