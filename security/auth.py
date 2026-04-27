import os

API_KEY = os.getenv("AICI_API_KEY", "change-me")

def verify(request):
    key = request.headers.get("x-api-key")
    return key == API_KEY