"""TrustOS Execution Dispatcher.

Narrows the TOCTOU window by re-verifying authority-state immediately
before the synthetic external commit. This is a reference boundary — not
cryptographic grant verification and not multi-host atomic commit.

See docs/contracts/TRUSTOS-RACE-001.md for frozen acceptance tests.
"""
from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from security.authority import AuthorityGrant
from security.external_adapter import EXTERNAL_DB, SyntheticExternalDB
from security.ledger import LivingLedger


@dataclass
class DispatchResult:
    success: bool
    message: str
    outcome_unknown: bool = False


class ExecutionDispatcher:
    def __init__(
        self,
        ledger: LivingLedger,
        *,
        external_db: SyntheticExternalDB | None = None,
        processed_path: str | None = None,
        latency_s: float = 0.05,
    ):
        self.ledger = ledger
        self.external = external_db if external_db is not None else EXTERNAL_DB
        self.latency_s = latency_s
        self._lock = threading.RLock()
        self._processed_path = Path(processed_path) if processed_path else None
        self._processed: dict[str, bool] = {}
        if self._processed_path and self._processed_path.exists():
            data = json.loads(self._processed_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self._processed = {k: bool(v) for k, v in data.items()}

    def _save_processed(self) -> None:
        if self._processed_path is None:
            return
        self._processed_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._processed_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._processed, sort_keys=True), encoding="utf-8")
        tmp.replace(self._processed_path)

    def _already_done(self, request_id: str) -> bool:
        if request_id in self._processed:
            return True
        if self.external.has_effect(request_id):
            self._processed[request_id] = True
            self._save_processed()
            return True
        return False

    def dispatch(
        self, request_id: str, action: str, grant: AuthorityGrant
    ) -> DispatchResult:
        with self._lock:
            if self._already_done(request_id):
                return DispatchResult(False, "Duplicate dispatch prevented")

            if not grant.is_valid():
                self.ledger.append(
                    event_type="DISPATCH_BLOCKED_REVOKED",
                    actor="system",
                    agent=grant.agent_id,
                    request_id=request_id,
                    artifact_id=action,
                )
                return DispatchResult(False, "Authority revoked or expired")

            if not grant.permits(action):
                self.ledger.append(
                    event_type="DISPATCH_BLOCKED_SCOPE",
                    actor="system",
                    agent=grant.agent_id,
                    request_id=request_id,
                    artifact_id=action,
                )
                return DispatchResult(False, "Action out of scope for grant")

            self.ledger.append(
                event_type="DISPATCH_INTENT",
                actor=grant.principal_id,
                agent=grant.agent_id,
                request_id=request_id,
                artifact_id=action,
            )

            try:
                # Artificial window so tests can revoke mid-dispatch (R03-A).
                if self.latency_s > 0:
                    time.sleep(self.latency_s)

                # Re-check authority-state at the effect boundary (not cryptographic).
                if not grant.is_valid():
                    self.ledger.append(
                        event_type="DISPATCH_ABORTED_LATE_REVOCATION",
                        actor="system",
                        agent=grant.agent_id,
                        request_id=request_id,
                        artifact_id=action,
                    )
                    return DispatchResult(
                        False, "Authority revoked during dispatch window"
                    )

                if not grant.permits(action):
                    self.ledger.append(
                        event_type="DISPATCH_BLOCKED_SCOPE",
                        actor="system",
                        agent=grant.agent_id,
                        request_id=request_id,
                        artifact_id=action,
                    )
                    return DispatchResult(False, "Action out of scope for grant")

                # Independently observable effect (not the ledger alone).
                self.external.commit_effect(request_id, action)

                try:
                    grant.consume()
                except Exception:
                    # Effect already committed; record uncertainty for recovery paths.
                    self.ledger.append(
                        event_type="DISPATCH_CONSUME_FAILED",
                        actor=grant.principal_id,
                        agent=grant.agent_id,
                        request_id=request_id,
                        artifact_id=action,
                    )

                self.ledger.append(
                    event_type="DISPATCH_SUCCESS",
                    actor=grant.principal_id,
                    agent=grant.agent_id,
                    request_id=request_id,
                    artifact_id=action,
                )
                self._processed[request_id] = True
                self._save_processed()
                return DispatchResult(True, "Execution successful")

            except Exception as e:
                self.ledger.append(
                    event_type="DISPATCH_FAILED",
                    actor=grant.principal_id,
                    agent=grant.agent_id,
                    request_id=request_id,
                    artifact_id=action,
                )
                return DispatchResult(False, str(e), outcome_unknown=True)
