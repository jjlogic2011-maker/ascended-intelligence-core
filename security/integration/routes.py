"""Flask blueprint: TrustOS tool-interceptor API routes.

Additive. Register with:
    from security.integration.routes import tool_bp, init_interceptor
    init_interceptor(app, ledger=LEDGER)
    app.register_blueprint(tool_bp)
"""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

tool_bp = Blueprint("trustos_tools", __name__)


def init_interceptor(app, *, ledger=None, interceptor=None):
    if interceptor is None:
        from security.integration.interceptor import build_default_interceptor
        interceptor = build_default_interceptor(ledger=ledger)
    app.config["TRUSTOS_INTERCEPTOR"] = interceptor
    return interceptor


def _ix():
    ix = current_app.config.get("TRUSTOS_INTERCEPTOR")
    if ix is None:
        from security.integration.interceptor import build_default_interceptor
        ix = build_default_interceptor()
        current_app.config["TRUSTOS_INTERCEPTOR"] = ix
    return ix


def _verify_api():
    try:
        from security.auth import verify
        return verify(request)
    except Exception:
        return True


def _verify_approver():
    try:
        from security.auth import verify_approver
        return verify_approver(request)
    except Exception:
        return True


def _approval_service():
    try:
        svc = current_app.config.get("APPROVAL_SERVICE")
        if svc is not None:
            return svc
        return None
    except Exception:
        return None


@tool_bp.route("/api/tool/health")
def tool_health():
    ix = _ix()
    return jsonify({
        "status": "ok",
        "interceptor": "ready",
        "pending_count": len(ix.list_pending()),
        "flow": "Tool Request -> Policy -> SHAPE -> Gate -> Engine -> Ledger -> Receipt",
    })


@tool_bp.route("/api/tool/preview", methods=["POST"])
def tool_preview():
    data = request.get_json(silent=True) or {}
    name = data.get("tool_name") or data.get("name") or ""
    if not name:
        return jsonify({"error": "tool_name required"}), 400
    from security.integration.interceptor import preview_policy
    return jsonify(preview_policy(name))


@tool_bp.route("/api/tool/preview/batch", methods=["POST"])
def tool_preview_batch():
    data = request.get_json(silent=True) or {}
    names = data.get("tool_names") or data.get("names") or []
    if not isinstance(names, list) or not names:
        return jsonify({"error": "tool_names list required"}), 400
    if len(names) > 50:
        return jsonify({"error": "max 50 tools per batch"}), 400
    return jsonify({"previews": _ix().batch_preview(names)})


@tool_bp.route("/api/tool", methods=["POST"])
def tool_submit():
    if not _verify_api():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    tool_name = data.get("tool_name") or data.get("name") or ""
    if not tool_name or not isinstance(tool_name, str):
        return jsonify({"error": "tool_name required"}), 400
    from security.integration.interceptor import ToolRequest
    tr = ToolRequest(
        tool_name=tool_name.strip(),
        arguments=data.get("arguments") or data.get("args") or {},
        agent_id=data.get("agent_id") or "model-agent",
        requester_id=data.get("requester_id") or data.get("agent_id") or "model-agent",
        model_request_id=data.get("model_request_id"),
        client_request_id=data.get("client_request_id"),
        metadata=data.get("metadata") or {},
    )
    if not isinstance(tr.arguments, dict):
        return jsonify({"error": "arguments must be an object"}), 400
    result = _ix().handle(tr)
    status = 202 if result.decision == "PENDING_HUMAN_APPROVAL" else 200
    if result.decision == "DENIED" and not result.executed:
        status = 403 if result.reason != "consequential action requires human approval" else 202
    return jsonify(result.to_dict()), status


@tool_bp.route("/api/tool/pending")
def tool_pending():
    if not _verify_approver():
        return jsonify({"error": "Approver credential required"}), 401
    return jsonify({"pending": _ix().list_pending()})


@tool_bp.route("/api/tool/resolve/<pending_id>", methods=["POST"])
def tool_resolve(pending_id):
    if not _verify_approver():
        return jsonify({"error": "Approver credential required"}), 401
    data = request.get_json(silent=True) or {}
    approve = bool(data.get("approve"))
    approval_id = data.get("approval_id")
    reason = data.get("reason") or ("denied by human" if not approve else None)
    result = _ix().resolve_pending(
        pending_id,
        approve=approve,
        approval_id=approval_id,
        approval_service=_approval_service() if approve else None,
        deny_reason=reason or "denied by human",
    )
    status = 200 if (result.executed or result.decision == "DENIED") else 403
    return jsonify(result.to_dict()), status


@tool_bp.route("/api/tool/<request_id>")
def tool_get(request_id):
    rec = _ix().get_result(request_id)
    if rec is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(rec)


@tool_bp.route("/api/tool/trail/<model_request_id>")
def tool_trail(model_request_id):
    trail = _ix().trail_by_model(model_request_id)
    return jsonify({
        "model_request_id": model_request_id,
        "count": len(trail),
        "results": trail,
    })


@tool_bp.route("/api/tool/compact/<request_id>")
def tool_compact(request_id):
    rec = _ix().get_result(request_id)
    if rec is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "request_id": request_id,
        "compact": rec.get("compact") or "",
        "decision": rec.get("decision"),
        "executed": rec.get("executed"),
    })
