"""Harness: one probe, one ledger row, no self-modification."""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from security.ledger import LivingLedger

from .wrapper import SandboxVerdict, probe_bubblewrap


class SandboxHarness:
    def __init__(self, ledger: Optional[LivingLedger] = None):
        self.ledger = ledger or LivingLedger()

    def run_probe(self, *, timeout_s: float = 5.0, runner=None) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        verdict: SandboxVerdict = probe_bubblewrap(timeout_s=timeout_s, runner=runner)
        event = self.ledger.append(
            event_type=f"SANDBOX_{verdict.verdict}",
            actor="sandbox-harness",
            agent="sandbox-probe",
            request_id=request_id,
            artifact_id="bwrap-true-probe",
        )
        return {
            "request_id": request_id,
            "receipt_event_id": event.event_id,
            **verdict.to_dict(),
            "scope": (
                "Tamper-evident against a missing or failed probe record. "
                "Not a container. Not Termux root. Not self-healing of the kernel."
            ),
        }
