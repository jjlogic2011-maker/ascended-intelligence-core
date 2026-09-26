"""TrustOS governance control loop (local simulation only).

Flow:
    request
    -> agent identity
    -> authority scope
    -> SHAPE authorization state
    -> policy check
    -> simulated action
    -> AIRI-DNA fingerprint
    -> Living Ledger receipt
    -> evidence record

No external side effects. The "action" is a local no-op returning a
structured record. This module does not call networks, files,
subprocesses, or third-party services.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from security.airi_dna import build_dna, fingerprint_content
from security.ledger import LivingLedger
from security.shape import Authorization, State


class GovernanceError(Exception):
    """Raised when governance preconditions fail."""


@dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    authority_scope: frozenset
    revoked: bool = False


@dataclass
class GovernanceRequest:
    request_id: str
    agent_id: str
    action: str
    artifact_id: str
    artifact_content: bytes
    creator: str
    version: str
    provenance: dict


@dataclass
class GovernanceResult:
    request_id: str
    decision: str
    executed: bool
    reason: str
    receipt_event_id: str | None = None
    fingerprint: str | None = None
    evidence: dict = field(default_factory=dict)


class GovernanceEngine:
    def __init__(self, *, ledger, agents, policies=None):
        self.ledger = ledger
        self.agents = agents
        self.policies = policies or {}
        self._seen_request_ids = set()

    def _identity(self, agent_id):
        agent = self.agents.get(agent_id)
        if agent is None:
            raise GovernanceError(f"unknown agent: {agent_id}")
        if agent.revoked:
            raise GovernanceError(f"agent revoked: {agent_id}")
        return agent

    def _authority(self, agent, action):
        required = self.policies.get(action)
        if required is None:
            raise GovernanceError(f"no policy for action: {action}")
        if not required.issubset(agent.authority_scope):
            raise GovernanceError(
                f"authority scope insufficient for action {action}"
            )

    def _audit(self, request, event_type):
        self.ledger.append(
            event_type=event_type,
            actor="governance",
            agent=request.agent_id,
            request_id=request.request_id,
            artifact_id=request.artifact_id,
        )

    def process(self, request, *, authorization, now=None):
        if request.request_id in self._seen_request_ids:
            self._audit(request, "DENIED")
            return GovernanceResult(
                request_id=request.request_id,
                decision="DENIED",
                executed=False,
                reason="replayed request",
            )

        try:
            agent = self._identity(request.agent_id)
            self._authority(agent, request.action)
        except GovernanceError as e:
            self._audit(request, "DENIED")
            return GovernanceResult(
                request_id=request.request_id,
                decision="DENIED",
                executed=False,
                reason=str(e),
            )

        if authorization.state == State.REVOKED:
            self._audit(request, "REVOKED")
            return GovernanceResult(
                request_id=request.request_id,
                decision="REVOKED",
                executed=False,
                reason="authorization revoked",
            )

        if authorization.is_expired(now):
            self._audit(request, "DENIED")
            return GovernanceResult(
                request_id=request.request_id,
                decision="DENIED",
                executed=False,
                reason="authorization expired",
            )

        if authorization.state != State.APPROVED:
            self._audit(request, "DENIED")
            return GovernanceResult(
                request_id=request.request_id,
                decision="DENIED",
                executed=False,
                reason=f"authorization not APPROVED (state={authorization.state.value})",
            )

        simulated_result = {
            "action": request.action,
            "artifact_id": request.artifact_id,
            "simulated": True,
        }

        content_hash = fingerprint_content(request.artifact_content)
        dna = build_dna(
            artifact_id=request.artifact_id,
            creator=request.creator,
            version=request.version,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            provenance=request.provenance,
            lineage=[],
            policy_state=State.EXECUTED.value,
            content_hash=content_hash,
        )
        fingerprint = dna.fingerprint()

        receipt = self.ledger.append(
            event_type=State.EXECUTED.value,
            actor=request.creator,
            agent=request.agent_id,
            request_id=request.request_id,
            artifact_id=request.artifact_id,
        )

        self._seen_request_ids.add(request.request_id)

        evidence = {
            "request_id": request.request_id,
            "agent_id": request.agent_id,
            "action": request.action,
            "artifact_id": request.artifact_id,
            "fingerprint": fingerprint,
            "receipt_event_id": receipt.event_id,
            "result": simulated_result,
        }

        return GovernanceResult(
            request_id=request.request_id,
            decision=State.EXECUTED.value,
            executed=True,
            reason="ok",
            receipt_event_id=receipt.event_id,
            fingerprint=fingerprint,
            evidence=evidence,
        )
