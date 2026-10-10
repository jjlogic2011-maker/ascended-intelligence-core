"""TrustOS memory_access.py — retrieval/action linkage layer.

Research kernel module. Not production-ready.
Adds auditability for reads that influence actions.

Event types:
- MEMORY_RETRIEVED
- MEMORY_USED_FOR_ACTION
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Iterable, Optional


def stable_hash(obj: object) -> str:
    """Return SHA-256 over canonical JSON."""
    blob = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


@dataclass(frozen=True)
class RetrievalReceipt:
    retrieval_id: str
    timestamp: float
    principal_id: str
    agent_id: str
    memory_ids: list
    query_hash: str
    purpose: str
    traversal_ids: list = field(default_factory=list)
    policy_version: str = "TOS-POL-v0.2"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ActionMemoryLink:
    link_id: str
    timestamp: float
    action_receipt_id: str
    retrieval_id: str
    influence: str = "supporting_context"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PromotionDecision:
    memory_id: str
    promote: bool
    reason: str
    score: float


@dataclass(frozen=True)
class RetentionDecision:
    memory_id: str
    decision: str
    reason: str


class MemoryAccessRecorder:
    """Small in-process recorder; replace lists with durable DB in production."""

    def __init__(self, ledger=None):
        self.ledger = ledger
        self.retrievals = {}
        self.links = {}

    def record_retrieval(
        self,
        *,
        principal_id: str,
        agent_id: str,
        memory_ids: Iterable,
        query_hash: str,
        purpose: str,
        traversal_ids: Optional[Iterable] = None,
        policy_version: str = "TOS-POL-v0.2",
    ) -> RetrievalReceipt:
        ids = list(memory_ids)
        if not principal_id or not agent_id:
            raise ValueError("principal_id and agent_id are required")
        if not ids:
            raise ValueError("at least one memory_id is required")
        if not query_hash:
            raise ValueError("query_hash is required")

        receipt = RetrievalReceipt(
            retrieval_id=str(uuid.uuid4()),
            timestamp=time.time(),
            principal_id=principal_id,
            agent_id=agent_id,
            memory_ids=ids,
            query_hash=query_hash,
            purpose=purpose,
            traversal_ids=list(traversal_ids or []),
            policy_version=policy_version,
        )
        self.retrievals[receipt.retrieval_id] = receipt

        if self.ledger:
            self.ledger.append(
                event_type="MEMORY_RETRIEVED",
                actor=principal_id,
                agent=agent_id,
                request_id=receipt.retrieval_id,
                artifact_id=",".join(ids),
            )
        return receipt

    def link_action_to_retrieval(
        self,
        *,
        action_receipt_id: str,
        retrieval_id: str,
        influence: str = "supporting_context",
    ) -> ActionMemoryLink:
        if retrieval_id not in self.retrievals:
            raise ValueError("unknown retrieval_id")
        if not action_receipt_id:
            raise ValueError("action_receipt_id is required")

        link = ActionMemoryLink(
            link_id=str(uuid.uuid4()),
            timestamp=time.time(),
            action_receipt_id=action_receipt_id,
            retrieval_id=retrieval_id,
            influence=influence,
        )
        self.links[link.link_id] = link

        if self.ledger:
            retrieval = self.retrievals[retrieval_id]
            self.ledger.append(
                event_type="MEMORY_USED_FOR_ACTION",
                actor=retrieval.principal_id,
                agent=retrieval.agent_id,
                request_id=action_receipt_id,
                artifact_id=retrieval_id,
            )
        return link


def should_promote_memory(
    *,
    memory_id: str,
    novelty_score: float,
    contradiction_score: float,
    use_count: int,
    risk_tier: str,
    human_approved: bool,
) -> PromotionDecision:
    """Promotion gate inspired by prediction-error filtering and consolidation."""
    score = novelty_score + contradiction_score + min(use_count, 10) / 10.0
    if risk_tier in {"high", "regulated", "public", "destructive"} and not human_approved:
        return PromotionDecision(memory_id, False, "high_risk_requires_human_approval", score)
    if human_approved:
        return PromotionDecision(memory_id, True, "human_approved", score)
    if contradiction_score >= 0.7:
        return PromotionDecision(memory_id, True, "contradiction_or_prediction_error", score)
    if novelty_score >= 0.75:
        return PromotionDecision(memory_id, True, "novel_memory", score)
    if use_count >= 5:
        return PromotionDecision(memory_id, True, "repeated_access", score)
    return PromotionDecision(memory_id, False, "insufficient_significance", score)


def schedule_forgetting(
    *,
    memory_id: str,
    retention_class: str,
    last_retrieved_at: Optional[float],
    dispute_status: str,
    now: Optional[float] = None,
) -> RetentionDecision:
    """Active forgetting policy. Does not silently delete."""
    now = now or time.time()
    if dispute_status in {"disputed", "legal_hold"}:
        return RetentionDecision(memory_id, "legal_hold", "dispute_or_legal_hold")
    if retention_class == "enterprise":
        return RetentionDecision(memory_id, "keep", "enterprise_retention")
    if retention_class == "session" and last_retrieved_at and (now - last_retrieved_at) > 60 * 60 * 24 * 30:
        return RetentionDecision(memory_id, "archive", "session_memory_stale")
    if retention_class == "delete_after_period" and last_retrieved_at and (now - last_retrieved_at) > 60 * 60 * 24 * 90:
        return RetentionDecision(memory_id, "delete", "retention_period_elapsed")
    return RetentionDecision(memory_id, "keep", "within_retention_policy")
