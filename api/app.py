import json
import uuid

from flask import Flask, request, jsonify

from core.orchestrator import Orchestrator
from security.auth import verify
from security.governance import (
    AgentIdentity,
    GovernanceEngine,
    GovernanceRequest,
)
from security.ledger import LivingLedger
from security.shape import Authorization, State

app = Flask(__name__)
orch = Orchestrator()

# ---------------------------------------------------------------------
# Governance kernel (process-wide)
# ---------------------------------------------------------------------
LEDGER = LivingLedger()

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


def _authorization_for_api(request_id):
    auth = Authorization(request_id=request_id)
    auth.transition(State.ASSESSED, actor="system")
    auth.transition(State.APPROVED, actor="api-caller")
    return auth


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@app.route("/")
def home():
    return {"message": "AICI Core Running"}


@app.route("/health")
def health():
    return {"status": "healthy"}


@app.route("/execute", methods=["POST"])
def execute():
    if not verify(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True)

    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid or missing JSON body"}), 200

    task_type = data.get("type", "report")
    action = {"report": "report", "security": "security"}.get(
        task_type, "execute"
    )

    request_id = str(uuid.uuid4())
    gov_request = GovernanceRequest(
        request_id=request_id,
        agent_id="api-agent",
        action=action,
        artifact_id=f"api-execute-{task_type}",
        artifact_content=json.dumps(data, sort_keys=True).encode("utf-8"),
        creator="api-caller",
        version="0.0.0",
        provenance={"source": "api/execute", "task_type": task_type},
    )

    auth = _authorization_for_api(request_id)
    gov_result = GOVERNANCE.process(gov_request, authorization=auth)

    if not gov_result.executed:
        return jsonify(
            {
                "error": "governance denied",
                "reason": gov_result.reason,
                "decision": gov_result.decision,
            }
        ), 200

    orch_result = orch.run(data)
    response = dict(orch_result) if isinstance(orch_result, dict) else {
        "result": orch_result
    }

    response["governance"] = {
        "decision": gov_result.decision,
        "agent_id": gov_request.agent_id,
        "request_id": request_id,
        "receipt_event_id": gov_result.receipt_event_id,
        "fingerprint": gov_result.fingerprint,
    }

    return jsonify(response)
