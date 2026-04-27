import os

CONFIG = {
    "env": os.getenv("ENV", "production"),
    "max_agents": int(os.getenv("AICI_MAX_AGENTS", "10"))
}
