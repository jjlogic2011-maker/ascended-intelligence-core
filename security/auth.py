import hmac
import os

API_KEY = os.getenv("AICI_API_KEY")
APPROVER_KEY = os.getenv("AICI_APPROVER_KEY")


def verify(request):
    key = request.headers.get("x-api-key")
    return bool(
        API_KEY
        and API_KEY != "change-me"
        and isinstance(key, str)
        and hmac.compare_digest(key, API_KEY)
    )


def approver_identity(credential, action=None, resource=None):
    """Reference shared-key approver; not a production human identity provider."""
    if not APPROVER_KEY or APPROVER_KEY == "change-me" or not isinstance(credential, str):
        return None
    try:
        if API_KEY and hmac.compare_digest(APPROVER_KEY, API_KEY):
            return None
        if hmac.compare_digest(credential, APPROVER_KEY):
            return "api-approver"
    except TypeError:
        return None
    return None


def verify_approver(request):
    return approver_identity(request.headers.get("x-approver-key")) is not None
