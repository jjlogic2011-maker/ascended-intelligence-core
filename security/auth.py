import os

API_KEY  = os.getenv("AICI_API_KEY", "change-me")
USERNAME = os.getenv("AICI_USERNAME", "admin")
PASSWORD = os.getenv("AICI_PASSWORD", "")


def verify(request):
    key = request.headers.get("x-api-key")
    return key == API_KEY


def login(username, password):
    if not PASSWORD:  # block login when password env var is unset
        return None
    if username == USERNAME and password == PASSWORD:
        return API_KEY
    return None
