import json
import uuid
import os
import threading
from dataclasses import asdict

from flask import Flask, request, jsonify

from core.orchestrator import Orchestrator
from security.auth import verify, verify_approver, approver_identity
from security.approval_service import ApprovalService
from security.human_gates import HUMAN_GATED_ACTIONS, is_gated
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


# Additive JSON action API. Pending state is process-local; actions are simulated.
PENDING = {}
PENDING_LOCK = threading.RLock()
ACTION_POLICIES = {**POLICIES, **{name: {"execute"} for name in HUMAN_GATED_ACTIONS}}
ACTION_GOVERNANCE = GovernanceEngine(
    ledger=LEDGER, agents=AGENTS, policies=ACTION_POLICIES
)


def get_approval_service():
    """Trusted issuance code may call .issue(); no public issuance route exists."""
    service = app.config.get("APPROVAL_SERVICE")
    if service is None:
        os.makedirs(app.instance_path, exist_ok=True)
        path = os.getenv("AICI_APPROVAL_DB", os.path.join(app.instance_path, "approvals.sqlite3"))
        service = ApprovalService(path, verify_human=approver_identity)
        app.config["APPROVAL_SERVICE"] = service
    return service


def _action_audit(record, event_type):
    return LEDGER.append(
        event_type=event_type, actor="api-approver", agent=record["agent_id"],
        request_id=record["pending_id"], artifact_id=record["resource"],
    )


def _run_action(record, approval_id=None):
    auth = Authorization(request_id=record["pending_id"])
    auth.transition(State.ASSESSED, actor="system")
    if is_gated(record["action"]):
        auth.transition(State.PENDING_HUMAN_APPROVAL, actor=record["requester_id"])
    auth.transition(State.APPROVED, actor="api-approver" if approval_id else "api-caller")
    gov_request = GovernanceRequest(
        request_id=record["pending_id"], agent_id=record["agent_id"],
        action=record["action"], artifact_id=record["resource"],
        artifact_content=json.dumps(record["arguments"], sort_keys=True,
                                    allow_nan=False).encode("utf-8"),
        creator=record["requester_id"], version="session10",
        provenance={"source": "api/action"},
    )
    return ACTION_GOVERNANCE.process(
        gov_request, authorization=auth, requester_id=record["requester_id"],
        arguments=record["arguments"], approval_id=approval_id,
        approval_service=get_approval_service() if approval_id else None,
    )


@app.route("/action", methods=["POST"])
def action():
    if not verify(request):
        return jsonify({"reason": "Unauthorized"}), 401
    data = request.get_json(silent=True)
    fields = {"action", "resource", "arguments", "agent_id", "requester_id"}
    if not isinstance(data, dict) or set(data) != fields:
        return jsonify({"reason": "Exact action request fields required"}), 400
    if (not isinstance(data["arguments"], dict) or
            any(not isinstance(data[k], str) or not data[k].strip()
                for k in fields - {"arguments"})):
        return jsonify({"reason": "Invalid request fields"}), 400
    try:
        record = json.loads(json.dumps(data, allow_nan=False))
    except (ValueError, TypeError):
        return jsonify({"reason": "Arguments must be finite JSON"}), 400
    record.update(pending_id=str(uuid.uuid4()), status="pending_approval")
    agent = AGENTS.get(record["agent_id"])
    required = ACTION_POLICIES.get(record["action"])
    if (agent is None or agent.revoked or required is None or
            not required.issubset(agent.authority_scope) or
            record["requester_id"] != record["agent_id"]):
        _action_audit(record, "DENIED")
        return jsonify({"reason": "Unknown action, agent, or insufficient bound authority"}), 403
    with PENDING_LOCK:
        if is_gated(record["action"]):
            _action_audit(record, "PENDING_HUMAN_APPROVAL")
            PENDING[record["pending_id"]] = record
            return jsonify({"status": "pending_approval", "pending_id": record["pending_id"],
                            "action": record["action"]}), 202
        result = _run_action(record)
        return jsonify(asdict(result)), 200 if result.executed else 403


@app.route("/approvals", methods=["GET"])
def approvals():
    if not verify_approver(request):
        return jsonify({"reason": "Approver credential required"}), 401
    with PENDING_LOCK:
        return jsonify([r for r in PENDING.values() if r["status"] == "pending_approval"])


@app.route("/approve/<pending_id>", methods=["POST"])
def approve(pending_id):
    if not verify_approver(request):
        return jsonify({"reason": "Approver credential required"}), 401
    with PENDING_LOCK:
        record = PENDING.get(pending_id)
        if record is None or record["status"] != "pending_approval":
            return jsonify({"reason": "No active pending request"}), 403
        data = request.get_json(silent=True)
        if (not isinstance(data, dict) or set(data) != {"approval_id"} or
                not isinstance(data["approval_id"], str) or not data["approval_id"].strip()):
            _action_audit(record, "DENIED")
            record["status"] = "failed"
            return jsonify({"reason": "Approval ID required"}), 403
        record["status"] = "processing"
        try:
            result = _run_action(record, data["approval_id"])
        except Exception:
            record["status"] = "failed"
            _action_audit(record, "DENIED")
            return jsonify({"reason": "Approval processing failed; request closed"}), 403
        record["status"] = "executed" if result.executed else "failed"
        return jsonify(asdict(result)), 200 if result.executed else 403


@app.route("/deny/<pending_id>", methods=["POST"])
def deny(pending_id):
    if not verify_approver(request):
        return jsonify({"reason": "Approver credential required"}), 401
    with PENDING_LOCK:
        record = PENDING.get(pending_id)
        if record is None or record["status"] != "pending_approval":
            return jsonify({"reason": "No active pending request"}), 403
        receipt = _action_audit(record, "DENIED")
        record["status"] = "denied"
        return jsonify({"status": "denied", "pending_id": pending_id,
                        "receipt_event_id": receipt.event_id})
