"""Flask entrypoint with TrustOS Desk registered.

  flask --app run_desk run --host=127.0.0.1 --port=5000
"""
from api.app import LEDGER, app, _pending_store
from ui.desk import register_desk

register_desk(
    app,
    get_pending=lambda: _pending_store().list_pending(),
    get_ledger=lambda: LEDGER,
)
application = app
