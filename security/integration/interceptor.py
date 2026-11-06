"""TrustOS Integration Interceptor — consequential action gate.

Flow:
    OpenAI-style Tool Request
        → TrustOS Policy classification
        → SHAPE Authorization state machine
        → Human gate (if consequential)
        → GovernanceEngine process
        → Living Ledger receipt
        → Evidence receipt returned to caller

Additive only. Does not replace the kernel.
Actions remain simulated unless a separate approved executor is wired.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from security.governance import (
    AgentIdentity,
    GovernanceEngine,
    GovernanceRequest,
    GovernanceResult,
)
from security.human_gates import HUMAN_GATED_ACTIONS, is_gated
from security.ledger import LivingLedger
from security.shape import Authorization, State


@dataclass
class ToolRequest:
    tool_name: str
    arguments: Dict[str, Any]
    agent_id: str = "model-agent"
    requester_id: str = "model-agent"
    model_request_id: Optional[str] = None
    client_request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def artifact_content(self) -> bytes:
        payload = {
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "model_request_id": self.model_request_id,
            "client_request_id": self.client_request_id,
            "metadata": self.metadata,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass
class InterceptorResult:
    request_id: str
    tool_name: str
    consequential: bool
    decision: str
    executed: bool
    reason: str
    pending_id: Optional[str] = None
    receipt_event_id: Optional[str] = None
    fingerprint: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    shape_state: Optional[str] = None
    compact: Optional[str] = None
    latency_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_compact(self) -> str:
        if self.decision == "PENDING_HUMAN_APPROVAL":
            return f"[GATE] {self.tool_name} → PENDING | id={self.pending_id or self.request_id[:8]}"
        if self.executed:
            return f"[OK] {self.tool_name} → EXECUTED | rx={self.receipt_event_id or '-'}"
        return f"[DENY] {self.tool_name} → {self.decision} | {self.reason[:40]}"


CONSEQUENTIAL_TOOLS = frozenset({
    "production_deploy", "credentials_access", "destructive_edit",
    "financial_action", "external_publication", "legal_filing",
    "irreversible_migration", "permission_escalation", "agent_creation",
    "policy_modification", "evidence_deletion", "security_control_disable",
    "bulk_data_export", "biometric_enrollment",
    "deploy", "delete_file", "write_secrets", "send_money", "publish",
})

_ALIAS = {
    "deploy": "production-deploy",
    "production_deploy": "production-deploy",
    "delete_file": "destructive-edit",
    "destructive_edit": "destructive-edit",
    "write_secrets": "credentials-access",
    "credentials_access": "credentials-access",
    "send_money": "financial-action",
    "financial_action": "financial-action",
    "publish": "external-publication",
    "external_publication": "external-publication",
}


def classify_tool(tool_name: str) -> str:
    normalized = tool_name.strip().lower().replace("-", "_")
    if normalized in CONSEQUENTIAL_TOOLS or is_gated(normalized):
        if normalized in HUMAN_GATED_ACTIONS:
            return normalized
        return _ALIAS.get(normalized, "production-deploy")
    return "execute"


def is_consequential(tool_name: str) -> bool:
    return is_gated(classify_tool(tool_name))


def preview_policy(tool_name: str) -> Dict[str, Any]:
    action = classify_tool(tool_name)
    gated = is_gated(action)
    return {
        "tool_name": tool_name,
        "trustos_action": action,
        "consequential": gated,
        "requires_human_approval": gated,
        "auto_executable": not gated,
    }


class TrustOSInterceptor:
    def __init__(self, *, engine: GovernanceEngine, ledger: LivingLedger,
                 agents: Optional[Dict[str, AgentIdentity]] = None,
                 default_agent_id: str = "model-agent"):
        self.engine = engine
        self.ledger = ledger
        self.agents = agents or {}
        self.default_agent_id = default_agent_id
        self._pending: Dict[str, Dict[str, Any]] = {}
        self._idempotency: Dict[str, Dict[str, Any]] = {}
        self._by_model: Dict[str, List[str]] = {}
        self._results: Dict[str, Dict[str, Any]] = {}

    def handle(self, tool_request: ToolRequest, *, approval_id: Optional[str] = None,
               approval_service=None, auto_approve_non_consequential: bool = True) -> InterceptorResult:
        start = time.time()
        if tool_request.client_request_id:
            cached = self._idempotency.get(tool_request.client_request_id)
            if cached is not None:
                r = InterceptorResult(**{k: cached[k] for k in InterceptorResult.__dataclass_fields__ if k in cached})
                r.latency_ms = round((time.time() - start) * 1000, 2)
                r.compact = r.to_compact()
                return r

        request_id = str(uuid.uuid4())
        action = classify_tool(tool_request.tool_name)
        consequential = is_gated(action)
        agent_id = tool_request.agent_id or self.default_agent_id

        auth = Authorization(request_id=request_id)
        auth.transition(State.ASSESSED, actor="interceptor")

        if consequential:
            auth.transition(State.PENDING_HUMAN_APPROVAL, actor=agent_id)
            if not approval_id or approval_service is None:
                pending_id = request_id
                self._pending[pending_id] = {
                    "tool_request": tool_request,
                    "action": action,
                    "auth": auth,
                    "created_at": time.time(),
                }
                self.ledger.append(
                    event_type="PENDING_HUMAN_APPROVAL",
                    actor="interceptor",
                    agent=agent_id,
                    request_id=request_id,
                    artifact_id=tool_request.tool_name,
                )
                result = InterceptorResult(
                    request_id=request_id,
                    tool_name=tool_request.tool_name,
                    consequential=True,
                    decision="PENDING_HUMAN_APPROVAL",
                    executed=False,
                    reason="consequential action requires human approval",
                    pending_id=pending_id,
                    shape_state=auth.state.value,
                )
                result.latency_ms = round((time.time() - start) * 1000, 2)
                result.compact = result.to_compact()
                self._store_result(tool_request, result)
                return result
            auth.transition(State.APPROVED, actor="human-approver")
        else:
            if not auto_approve_non_consequential:
                result = InterceptorResult(
                    request_id=request_id,
                    tool_name=tool_request.tool_name,
                    consequential=False,
                    decision="DENIED",
                    executed=False,
                    reason="non-consequential auto-approve disabled",
                    shape_state=auth.state.value,
                )
                result.latency_ms = round((time.time() - start) * 1000, 2)
                result.compact = result.to_compact()
                return result
            auth.transition(State.APPROVED, actor="interceptor")

        gov_request = GovernanceRequest(
            request_id=request_id,
            agent_id=agent_id,
            action=action,
            artifact_id=tool_request.tool_name,
            artifact_content=tool_request.artifact_content(),
            creator=tool_request.requester_id,
            version="interceptor-2",
            provenance={
                "source": "trustos_interceptor",
                "tool_name": tool_request.tool_name,
                "model_request_id": tool_request.model_request_id,
                "client_request_id": tool_request.client_request_id,
            },
        )

        gov_result: GovernanceResult = self.engine.process(
            gov_request,
            authorization=auth,
            approval_service=approval_service,
            approval_id=approval_id,
            requester_id=tool_request.requester_id,
            arguments=tool_request.arguments,
        )

        result = InterceptorResult(
            request_id=request_id,
            tool_name=tool_request.tool_name,
            consequential=consequential,
            decision=gov_result.decision,
            executed=gov_result.executed,
            reason=gov_result.reason,
            receipt_event_id=gov_result.receipt_event_id,
            fingerprint=gov_result.fingerprint,
            evidence=gov_result.evidence or {},
            shape_state=auth.state.value,
        )
        result.latency_ms = round((time.time() - start) * 1000, 2)
        result.compact = result.to_compact()
        self._store_result(tool_request, result)
        return result

    def _store_result(self, tool_request: ToolRequest, result: InterceptorResult) -> None:
        d = result.to_dict()
        self._results[result.request_id] = d
        if tool_request.client_request_id:
            self._idempotency[tool_request.client_request_id] = d
        if tool_request.model_request_id:
            self._by_model.setdefault(tool_request.model_request_id, []).append(result.request_id)

    def list_pending(self) -> List[Dict[str, Any]]:
        out = []
        for pid, rec in self._pending.items():
            tr: ToolRequest = rec["tool_request"]
            out.append({
                "pending_id": pid,
                "tool_name": tr.tool_name,
                "action": rec["action"],
                "arguments": tr.arguments,
                "agent_id": tr.agent_id,
                "model_request_id": tr.model_request_id,
                "created_at": rec["created_at"],
            })
        return out

    def resolve_pending(self, pending_id: str, *, approve: bool,
                        approval_id: Optional[str] = None, approval_service=None,
                        actor: str = "human-approver",
                        deny_reason: str = "denied by human") -> InterceptorResult:
        rec = self._pending.pop(pending_id, None)
        if rec is None:
            r = InterceptorResult(
                request_id=pending_id, tool_name="", consequential=True,
                decision="DENIED", executed=False, reason="no active pending request",
            )
            r.compact = r.to_compact()
            return r
        tool_request: ToolRequest = rec["tool_request"]
        if not approve:
            self.ledger.append(
                event_type="DENIED", actor=actor, agent=tool_request.agent_id,
                request_id=pending_id, artifact_id=tool_request.tool_name,
            )
            r = InterceptorResult(
                request_id=pending_id, tool_name=tool_request.tool_name,
                consequential=True, decision="DENIED", executed=False,
                reason=deny_reason, shape_state=State.DENIED.value,
            )
            r.compact = r.to_compact()
            self._store_result(tool_request, r)
            return r
        return self.handle(
            tool_request, approval_id=approval_id,
            approval_service=approval_service, auto_approve_non_consequential=False,
        )

    def get_result(self, request_id: str) -> Optional[Dict[str, Any]]:
        return self._results.get(request_id)

    def trail_by_model(self, model_request_id: str) -> List[Dict[str, Any]]:
        ids = self._by_model.get(model_request_id, [])
        return [self._results[i] for i in ids if i in self._results]

    def batch_preview(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        return [preview_policy(n) for n in tool_names]


def build_default_interceptor(ledger: Optional[LivingLedger] = None) -> TrustOSInterceptor:
    ledger = ledger or LivingLedger()
    agents = {
        "model-agent": AgentIdentity(
            agent_id="model-agent",
            authority_scope=frozenset({"read", "write", "execute"}),
        ),
        "api-agent": AgentIdentity(
            agent_id="api-agent",
            authority_scope=frozenset({"read", "write", "execute"}),
        ),
    }
    policies = {
        "read": {"read"},
        "write": {"write"},
        "execute": {"execute"},
        "report": {"read", "write"},
        "security": {"execute"},
    }
    for gated in HUMAN_GATED_ACTIONS:
        policies[gated] = {"execute"}
    engine = GovernanceEngine(ledger=ledger, agents=agents, policies=policies)
    return TrustOSInterceptor(engine=engine, ledger=ledger, agents=agents)
