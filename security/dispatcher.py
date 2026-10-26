"""TrustOS Execution Dispatcher.

Closes the TOCTOU (Time-of-Check to Time-of-Use) gap by re-verifying
authority immediately before executing the action.
"""
import time
from dataclasses import dataclass
from security.authority import AuthorityGrant
from security.ledger import LivingLedger
from security.external_adapter import EXTERNAL_DB

@dataclass
class DispatchResult:
    success: bool
    message: str
    outcome_unknown: bool = False

class ExecutionDispatcher:
    def __init__(self, ledger: LivingLedger):
        self.ledger = ledger
        self._processed = {}

    def dispatch(self, request_id: str, action: str, grant: AuthorityGrant) -> DispatchResult:
        if request_id in self._processed:
            return DispatchResult(False, "Duplicate dispatch prevented")

        if not grant.is_valid():
            self.ledger.append(event_type="DISPATCH_BLOCKED_REVOKED", actor="system", agent=grant.agent_id, request_id=request_id, artifact_id=action)
            return DispatchResult(False, "Authority revoked or expired")

        if not grant.permits(action):
             self.ledger.append(event_type="DISPATCH_BLOCKED_SCOPE", actor="system", agent=grant.agent_id, request_id=request_id, artifact_id=action)
             return DispatchResult(False, "Action out of scope for grant")

        self.ledger.append(event_type="DISPATCH_INTENT", actor=grant.principal_id, agent=grant.agent_id, request_id=request_id, artifact_id=action)

        try:
            # 1. Simulate network/setup latency BEFORE the effect commits
            time.sleep(0.05) 
            
            # 2. R01/R03-A: Atomic Re-check (The TOCTOU closure)
            if not grant.is_valid():
                self.ledger.append(event_type="DISPATCH_ABORTED_LATE_REVOCATION", actor="system", agent=grant.agent_id, request_id=request_id, artifact_id=action)
                return DispatchResult(False, "Authority revoked during dispatch window")

            # 3. Execute the actual external effect
            EXTERNAL_DB.commit_effect(request_id, action)
            
            self.ledger.append(event_type="DISPATCH_SUCCESS", actor=grant.principal_id, agent=grant.agent_id, request_id=request_id, artifact_id=action)
            self._processed[request_id] = True
            return DispatchResult(True, "Execution successful")

        except Exception as e:
            self.ledger.append(event_type="DISPATCH_FAILED", actor=grant.principal_id, agent=grant.agent_id, request_id=request_id, artifact_id=action)
            return DispatchResult(False, str(e), outcome_unknown=True)
