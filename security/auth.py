import hmac
import os

API_KEY = os.getenv("AICI_API_KEY")


def verify(request):
    key = request.headers.get("x-api-key")
    return bool(
        API_KEY
        and API_KEY != "change-me"
        and isinstance(key, str)
        and hmac.compare_digest(key, API_KEY)
    )
