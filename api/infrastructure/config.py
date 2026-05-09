import os

def _parse_max_agents(value, default=10):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

CONFIG = {
    "env": os.getenv("ENV", "production"),
    "max_agents": _parse_max_agents(os.getenv("AICI_MAX_AGENTS"))
}
