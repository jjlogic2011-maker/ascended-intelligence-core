"""Deny-by-default execution sandbox adapter.

Bubblewrap (bwrap) is the Linux probe. Termux/Android without user
namespaces cannot host that probe. Missing bwrap is UNVERIFIABLE, never PASS.
"""

from .wrapper import (
    CONTROLS_22,
    SandboxPlan,
    SandboxVerdict,
    build_probe_plan,
    probe_bubblewrap,
)
from .harness import SandboxHarness

__all__ = [
    "CONTROLS_22",
    "SandboxHarness",
    "SandboxPlan",
    "SandboxVerdict",
    "build_probe_plan",
    "probe_bubblewrap",
]
