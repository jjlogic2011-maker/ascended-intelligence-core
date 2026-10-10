import json
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
PENDING_LOCK = threading.RLock()


def _pending_store():
    store = app.config.get("PENDING_STORE")
    if store is None:
        os.makedirs(app.instance_path, exist_ok=True)
        db_path = os.getenv("AICI_PENDING_DB", os.path.join(app.instance_path, "pending.sqlite3"))
        store = PendingStore(db_path)
        app.config["PENDING_STORE"] = store
    return store
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
            _pending_store().put(record["pending_id"], record)
            return jsonify({"status": "pending_approval", "pending_id": record["pending_id"],
                            "action": record["action"]}), 202
        result = _run_action(record)
        return jsonify(asdict(result)), 200 if result.executed else 403


@app.route("/approvals", methods=["GET"])
def approvals():
    if not verify_approver(request):
        return jsonify({"reason": "Approver credential required"}), 401
    return jsonify(_pending_store().list_pending())


def _do_approve(pending_id, approval_id):
    """Shared approve logic. Returns (body_dict, http_status)."""
    store = _pending_store()
    record = store.get(pending_id)
    if record is None or record["status"] != "pending_approval":
        return {"reason": "No active pending request"}, 403
    store.update_status(pending_id, "processing")
    try:
        result = _run_action(record, approval_id)
    except Exception:
        store.update_status(pending_id, "failed")
        _action_audit(record, "DENIED")
        return {"reason": "Approval processing failed; request closed"}, 403
    store.update_status(pending_id, "executed" if result.executed else "failed")
    return asdict(result), 200 if result.executed else 403


def _do_deny(pending_id):
    """Shared deny logic. Returns (body_dict, http_status)."""
    store = _pending_store()
    record = store.get(pending_id)
    if record is None or record["status"] != "pending_approval":
        return {"reason": "No active pending request"}, 403
    receipt = _action_audit(record, "DENIED")
    store.update_status(pending_id, "denied")
    return {
        "status": "denied",
        "pending_id": pending_id,
        "receipt_event_id": receipt.event_id,
    }, 200



@app.route("/approve/<pending_id>", methods=["POST"])
def approve(pending_id):
    if not verify_approver(request):
        return jsonify({"reason": "Approver credential required"}), 401
    data = request.get_json(silent=True)
    if (not isinstance(data, dict) or set(data) != {"approval_id"} or
            not isinstance(data["approval_id"], str) or not data["approval_id"].strip()):
        store = _pending_store()
        record = store.get(pending_id)
        if record is not None and record["status"] == "pending_approval":
            _action_audit(record, "DENIED")
            store.update_status(pending_id, "failed")
        return jsonify({"reason": "Approval ID required"}), 403
    body, status = _do_approve(pending_id, data["approval_id"])
    return jsonify(body), status


@app.route("/deny/<pending_id>", methods=["POST"])
def deny(pending_id):
    if not verify_approver(request):
        return jsonify({"reason": "Approver credential required"}), 401
    body, status = _do_deny(pending_id)
    return jsonify(body), status



# ---------------------------------------------------------------------
from flask import session, redirect, url_for, render_template_string
from security.ui_auth import is_ui_enabled, verify_ui_key

app.secret_key = os.getenv("AICI_UI_SECRET", os.urandom(24))


UI_LOGIN_HTML = """<!doctype html>
<html><head><title>TrustOS Approval — Login</title></head>
<body style="font-family:system-ui;max-width:420px;margin:5em auto;padding:0 1em;">
<h1>TrustOS Approval</h1>
<p style="color:#666;">Sign in to review pending agent actions.</p>
{% if error %}<p style="color:#b00;"><strong>{{ error }}</strong></p>{% endif %}
<form method="post" action="{{ url_for('ui_login') }}">
  <label style="display:block;margin-bottom:8px;">
    UI key:
    <input type="password" name="key" autofocus
           style="width:100%;padding:8px;margin-top:4px;font-family:monospace;">
  </label>
  <button type="submit" style="padding:8px 16px;">Sign in</button>
</form>
</body></html>
"""


UI_INDEX_HTML = """<!doctype html>
<html><head><title>TrustOS — Pending Approvals</title></head>
<body style="font-family:system-ui;max-width:1100px;margin:2em auto;padding:0 1em;">
<h1>Pending Approvals</h1>
<p><a href="{{ url_for('ui_logout') }}">Sign out</a></p>
{% if message %}<p style="color:#060;"><strong>{{ message }}</strong></p>{% endif %}
{% if not pending %}
  <p style="color:#666;"><em>No pending requests.</em></p>
{% else %}
<table border="1" cellpadding="8" cellspacing="0"
       style="border-collapse:collapse;width:100%;font-size:14px;">
<thead style="background:#f0f0f0;">
<tr>
  <th>pending_id</th><th>action</th><th>resource</th>
  <th>agent</th><th>approval_id</th><th></th>
</tr>
</thead>
<tbody>
{% for r in pending %}
<tr>
  <td><code style="font-size:12px;">{{ r.pending_id }}</code></td>
  <td>{{ r.action }}</td>
  <td>{{ r.resource }}</td>
  <td>{{ r.agent_id }}</td>
  <td>
    <form method="post"
          action="{{ url_for('ui_approve', pending_id=r.pending_id) }}"
          style="display:inline;">
      <input name="approval_id" placeholder="approval_id" required
             style="padding:4px;width:18em;font-family:monospace;">
      <button type="submit" style="padding:6px 12px;">Approve</button>
    </form>
  </td>
  <td>
    <form method="post"
          action="{{ url_for('ui_deny', pending_id=r.pending_id) }}"
          style="display:inline;">
      <button type="submit" style="padding:6px 12px;">Deny</button>
    </form>
  </td>
</tr>
{% endfor %}
</tbody>
</table>
{% endif %}
</body></html>
"""


@app.route("/ui/login", methods=["GET", "POST"])
def ui_login():
    if not is_ui_enabled():
        return "UI not configured (AICI_UI_KEY unset)", 503
    if request.method == "POST":
        key = request.form.get("key", "")
        if verify_ui_key(key):
            session["ui_authed"] = True
            return redirect(url_for("ui_index"))
        return render_template_string(UI_LOGIN_HTML, error="Invalid key"), 401
    return render_template_string(UI_LOGIN_HTML, error=None)


@app.route("/ui/logout")
def ui_logout():
    session.pop("ui_authed", None)
    return redirect(url_for("ui_login"))


@app.route("/ui")
def ui_index():
    if not is_ui_enabled():
        return "UI not configured (AICI_UI_KEY unset)", 503
    if not session.get("ui_authed"):
        return redirect(url_for("ui_login"))
    pending = _pending_store().list_pending()
    message = request.args.get("message")
    return render_template_string(UI_INDEX_HTML, pending=pending, message=message)


@app.route("/ui/approve/<pending_id>", methods=["POST"])
def ui_approve(pending_id):
    if not is_ui_enabled():
        return "UI not configured (AICI_UI_KEY unset)", 503
    if not session.get("ui_authed"):
        return redirect(url_for("ui_login"))
    approval_id = (request.form.get("approval_id") or "").strip()
    if not approval_id:
        return redirect(url_for("ui_index", message="approval_id required"))
    body, _status = _do_approve(pending_id, approval_id)
    msg = "Approved and executed." if body.get("executed") else body.get("reason", "Approval failed.")
    return redirect(url_for("ui_index", message=msg))


@app.route("/ui/deny/<pending_id>", methods=["POST"])
def ui_deny(pending_id):
    if not is_ui_enabled():
        return "UI not configured (AICI_UI_KEY unset)", 503
    if not session.get("ui_authed"):
        return redirect(url_for("ui_login"))
    body, _status = _do_deny(pending_id)
    msg = "Denied." if body.get("status") == "denied" else body.get("reason", "Deny failed.")
    return redirect(url_for("ui_index", message=msg))
