"""TrustOS UI session authentication.

Simple session-gated access for the human approval interface.
Enabled only if AICI_UI_KEY is set. If unset, all /ui/* routes
return 503 (fail closed). Not production-grade authentication;
a session-scoped shared key for demonstration purposes.

Production requires a real identity provider (OIDC, WebAuthn).
"""
from __future__ import annotations

import hmac
import os


class UIAuthError(Exception):
    """Raised when the UI is not properly configured."""


def get_ui_key() -> str | None:
    key = os.getenv("AICI_UI_KEY")
    if not key or key == "change-me":
        return None
    return key


def is_ui_enabled() -> bool:
    return get_ui_key() is not None


def verify_ui_key(provided: str | None) -> bool:
    expected = get_ui_key()
    if expected is None:
        return False
    if not isinstance(provided, str) or not provided.strip():
        return False
    return hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))
