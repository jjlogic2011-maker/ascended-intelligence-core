"""TrustOS telemetry and observability.

Records operational metrics directly into the Living Ledger.
This ensures that denials, executions, and errors are not just
transient HTTP responses, but permanent audit evidence.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from security.ledger import LivingLedger

class TelemetryEngine:
    def __init__(self, ledger: LivingLedger):
        self.ledger = ledger

    def record_execution(self, action: str, agent_id: str, request_id: str) -> None:
        self.ledger.append(
            event_type="TELEMETRY_EXECUTED",
            actor="system",
            agent=agent_id,
            request_id=request_id,
            artifact_id=action,
        )

    def record_denial(self, action: str, agent_id: str, reason: str) -> None:
        self.ledger.append(
            event_type="TELEMETRY_DENIED",
            actor="system",
            agent=agent_id,
            request_id=f"denied-{int(time.time())}",
            artifact_id=action,
        )

    def get_metrics(self) -> dict:
        events = self.ledger.events
        total = len(events)
        denials = sum(1 for e in events if e.event_type == "TELEMETRY_DENIED")
        executions = sum(1 for e in events if e.event_type == "TELEMETRY_EXECUTED")

        return {
            "total_events": total,
            "executions": executions,
            "denials": denials,
            "error_rate": (denials / total) if total > 0 else 0.0,
            "ledger_intact": self.ledger.verify()[0]
        }
