"""Deterministic Agent Reliability Controller."""
from __future__ import annotations
from dataclasses import dataclass
from security.ledger import LivingLedger

@dataclass
class ReliabilityResult:
    allowed: bool
    reason: str

class ReliabilityController:
    def __init__(self, ledger: LivingLedger, max_failures: int = 3):
        self.ledger = ledger
        self.max_failures = max_failures
        self._failure_counts = {}

    def check_quota(self, agent_id: str) -> ReliabilityResult:
        failures = self._failure_counts.get(agent_id, 0)
        if failures >= self.max_failures:
            self.ledger.append(
                event_type="AGENT_QUARANTINED",
                actor="system", agent=agent_id, request_id="quarantine-check", artifact_id="reliability"
            )
            return ReliabilityResult(False, f"Agent {agent_id} quarantined due to {failures} failures")
        return ReliabilityResult(True, "Agent within reliability bounds")

    def record_failure(self, agent_id: str) -> None:
        self._failure_counts[agent_id] = self._failure_counts.get(agent_id, 0) + 1

    def record_success(self, agent_id: str) -> None:
        self._failure_counts[agent_id] = 0
