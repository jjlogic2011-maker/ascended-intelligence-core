"""Flask entrypoint with TrustOS Desk registered.

Usage:
  export AICI_UI_KEY=...
  export AICI_UI_SECRET=...
  flask --app run_desk run --host=127.0.0.1 --port=5000

Then open /ui/login and /desk.
"""
from api.app import LEDGER, app, _pending_store
from ui.desk import register_desk

register_desk(
    app,
    get_pending=lambda: _pending_store().list_pending(),
    get_ledger=lambda: LEDGER,
)

# WSGI/Flask discovery
application = app
