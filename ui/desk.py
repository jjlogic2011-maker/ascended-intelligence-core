"""TrustOS Desk — operator UI beyond the minimal approval table.

Registers /desk routes on the Flask app. Reuses UI key session auth.
Does not claim production multi-tenant SSO.
"""
from __future__ import annotations

from flask import redirect, render_template_string, request, session, url_for

from security.ui_auth import is_ui_enabled, verify_ui_key

DESK_HTML = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>TrustOS Desk</title>
  <style>
    :root { --bg:#0f1419; --panel:#1a2332; --text:#e7ecf3; --muted:#8b9bb4; --accent:#3d8bfd; --ok:#3dd68c; --warn:#f5a524; --bad:#f31260; --border:#2a3548; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: ui-sans-serif, system-ui, sans-serif; background:var(--bg); color:var(--text); line-height:1.45; }
    header { display:flex; justify-content:space-between; align-items:center; padding:1rem 1.5rem; border-bottom:1px solid var(--border); background:var(--panel); }
    header h1 { font-size:1.1rem; margin:0; }
    header a { color:var(--muted); text-decoration:none; margin-left:1rem; font-size:0.9rem; }
    header a:hover { color:var(--accent); }
    main { max-width:1100px; margin:0 auto; padding:1.25rem; }
    .grid { display:grid; gap:1rem; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); }
    .card { background:var(--panel); border:1px solid var(--border); border-radius:12px; padding:1rem 1.1rem; }
    .card h2 { margin:0 0 0.5rem; font-size:0.85rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.06em; }
    .metric { font-size:1.6rem; font-weight:650; }
    .ok { color:var(--ok); } .warn { color:var(--warn); }
    table { width:100%; border-collapse:collapse; font-size:0.85rem; }
    th, td { text-align:left; padding:0.55rem 0.4rem; border-bottom:1px solid var(--border); vertical-align:top; }
    th { color:var(--muted); font-weight:600; }
    code { font-size:0.78rem; color:#c5d4f0; }
    .actionsform { display:inline; }
    input[type=text] { background:var(--bg); border:1px solid var(--border); color:var(--text); padding:0.35rem 0.5rem; border-radius:6px; width:12rem; }
    button { background:var(--accent); color:#fff; border:0; border-radius:6px; padding:0.4rem 0.75rem; cursor:pointer; font-weight:600; }
    button.deny { background:var(--bad); }
    .banner { padding:0.75rem 1rem; border-radius:8px; background:#1c2a22; color:var(--ok); margin-bottom:1rem; }
    .note { color:var(--muted); font-size:0.85rem; margin-top:1rem; }
  </style>
</head>
<body>
<header>
  <h1>TrustOS Desk</h1>
  <nav>
    <a href=\"{{ url_for('desk_home') }}\">Desk</a>
    <a href=\"{{ url_for('ui_index') }}\">Classic approvals</a>
    <a href=\"{{ url_for('ui_logout') }}\">Sign out</a>
  </nav>
</header>
<main>
  {% if message %}<div class=\"banner\">{{ message }}</div>{% endif %}
  <div class=\"grid\">
    <div class=\"card\"><h2>Pending approvals</h2><div class=\"metric {% if pending_count %}warn{% else %}ok{% endif %}\">{{ pending_count }}</div></div>
    <div class=\"card\"><h2>Ledger events (tip window)</h2><div class=\"metric\">{{ ledger_count }}</div></div>
    <div class=\"card\"><h2>TRUSTOS-RACE-001</h2><div class=\"metric ok\" style=\"font-size:1rem;\">Reference boundary</div>
      <p class=\"note\" style=\"margin:0.4rem 0 0;\">Synthetic sink · authority-state re-check · not multi-host finality</p></div>
  </div>
  <div class=\"card\" style=\"margin-top:1rem;\"><h2>Queue</h2>
    {% if not pending %}<p class=\"note\">No pending agent actions.</p>{% else %}
    <table><thead><tr><th>pending_id</th><th>action</th><th>resource</th><th>agent</th><th></th></tr></thead><tbody>
    {% for r in pending %}<tr>
      <td><code>{{ r.pending_id }}</code></td><td>{{ r.action }}</td><td>{{ r.resource }}</td><td>{{ r.agent_id }}</td>
      <td>
        <form class=\"actionsform\" method=\"post\" action=\"{{ url_for('ui_approve', pending_id=r.pending_id) }}\">
          <input type=\"text\" name=\"approval_id\" placeholder=\"approval_id\" required>
          <button type=\"submit\">Approve</button></form>
        <form class=\"actionsform\" method=\"post\" action=\"{{ url_for('ui_deny', pending_id=r.pending_id) }}\">
          <button class=\"deny\" type=\"submit\">Deny</button></form>
      </td></tr>{% endfor %}
    </tbody></table>{% endif %}
  </div>
  <div class=\"card\" style=\"margin-top:1rem;\"><h2>Recent ledger tip</h2>
    {% if not recent_events %}<p class=\"note\">No events in process ledger yet.</p>{% else %}
    <table><thead><tr><th>type</th><th>request</th><th>agent</th><th>artifact</th></tr></thead><tbody>
    {% for e in recent_events %}<tr>
      <td><code>{{ e.event_type }}</code></td><td><code>{{ e.request_id }}</code></td>
      <td>{{ e.agent }}</td><td>{{ e.artifact_id }}</td></tr>{% endfor %}
    </tbody></table>{% endif %}
  </div>
  <p class=\"note\">Desk is an operator convenience surface. Authorization remains on API/dispatcher paths.</p>
</main></body></html>
"""


def register_desk(app, *, get_pending, get_ledger):
    def _require_ui():
        if not is_ui_enabled():
            return "UI not configured (AICI_UI_KEY unset)", 503
        if not session.get("ui_authed"):
            return redirect(url_for("ui_login"))
        return None

    @app.route("/desk")
    def desk_home():
        gate = _require_ui()
        if gate is not None:
            return gate
        pending = get_pending() or []
        ledger = get_ledger()
        events = list(getattr(ledger, "events", []) or [])
        recent = events[-12:][::-1]
        recent_view = [{
            "event_type": getattr(e, "event_type", ""),
            "request_id": getattr(e, "request_id", ""),
            "agent": getattr(e, "agent", ""),
            "artifact_id": getattr(e, "artifact_id", ""),
        } for e in recent]
        return render_template_string(
            DESK_HTML,
            pending=pending,
            pending_count=len(pending),
            ledger_count=len(events),
            recent_events=recent_view,
            message=request.args.get("message"),
        )
