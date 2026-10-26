import json
import time
import uuid
import os
import threading
from dataclasses import asdict

from flask import Flask, request, jsonify

from core.orchestrator import Orchestrator
from security.auth import verify, verify_approver, approver_identity
from security.pending_store import PendingStore
from security.approval_service import ApprovalService
from security.human_gates import HUMAN_GATED_ACTIONS, is_gated
from security.governance import (
    AgentIdentity,
    GovernanceEngine,
    GovernanceRequest,
)
from security.ledger import LivingLedger
from security.telemetry import TelemetryEngine
from security.export import generate_export, verify_export
from security.shape import Authorization, State

app = Flask(__name__)
orch = Orchestrator()

# ---------------------------------------------------------------------
# Governance kernel (process-wide)
# ---------------------------------------------------------------------
_ledger_path = os.getenv("AICI_LEDGER_PATH")
LEDGER = LivingLedger(path=_ledger_path) if _ledger_path else LivingLedger()

AGENTS = {
    "api-agent": AgentIdentity(
        agent_id="api-agent",
        authority_scope=frozenset({"read", "write", "execute"}),
    ),
}

POLICIES = {
    "read": {"read"},
    "write": {"write"},
    "execute": {"execute"},
    "report": {"read", "write"},
    "security": {"execute"},
}

GOVERNANCE = GovernanceEngine(ledger=LEDGER, agents=AGENTS, policies=POLICIES)
TELEMETRY = TelemetryEngine(LEDGER)


def _authorization_for_api(request_id):
    auth = Authorization(request_id=request_id)
    auth.transition(State.ASSESSED, actor="system")
    auth.transition(State.APPROVED, actor="api-caller")
    return auth
