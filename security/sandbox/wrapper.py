"""Bubblewrap plan + fixed probe. Caller argv is never executed."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

CONTROLS_22: Tuple[str, ...] = (
    "deny_by_default",
    "fixed_probe_only",
    "three_verdict",
    "timeout_not_pass",
    "bwrap_argv_no_shell",
    "unshare_net",
    "unshare_pid",
    "ro_bind_usr",
    "new_session",
    "die_with_parent",
    "clearenv",
    "landlock_fallback",
    "seatbelt_macos",
    "termux_no_userns",
    "proot_is_not_root",
    "no_token_passthrough",
    "arg_schema",
    "named_grant_approver",
    "trajectory_score",
    "correction_closure",
    "response_scan",
    "offline_evidence_pack",
)


@dataclass
class SandboxPlan:
    backend: str
    argv: List[str]
    network: str = "none"
    controls: Sequence[str] = field(default_factory=lambda: CONTROLS_22)

    def to_dict(self) -> dict:
        return {
            "backend": self.backend,
            "argv": list(self.argv),
            "network": self.network,
            "control_count": len(self.controls),
        }


@dataclass
class SandboxVerdict:
    verdict: str
    reason: str
    backend: str
    exit_code: Optional[int] = None
    bwrap_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "reason": self.reason,
            "backend": self.backend,
            "exit_code": self.exit_code,
            "bwrap_path": self.bwrap_path,
        }


def build_probe_plan(bwrap: str = "bwrap") -> SandboxPlan:
    argv = [
        bwrap,
        "--ro-bind", "/usr", "/usr",
        "--unshare-net",
        "--unshare-pid",
        "--new-session",
        "--die-with-parent",
        "--",
        "/bin/true",
    ]
    return SandboxPlan(backend="bubblewrap", argv=argv, network="none")


def probe_bubblewrap(*, timeout_s: float = 5.0, runner=None) -> SandboxVerdict:
    path = shutil.which("bwrap")
    if path is None and runner is None:
        return SandboxVerdict(
            verdict="UNVERIFIABLE",
            reason="bwrap not on PATH; Termux/Android often cannot provide user namespaces",
            backend="none",
        )
    plan = build_probe_plan(path or "bwrap")
    try:
        if runner is not None:
            code, err = runner(plan.argv, timeout_s)
        else:
            proc = subprocess.run(
                plan.argv,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
            code, err = proc.returncode, (proc.stderr or "")[:200]
    except subprocess.TimeoutExpired:
        return SandboxVerdict(
            verdict="UNVERIFIABLE",
            reason="probe timed out; timeout is not a pass",
            backend="bubblewrap",
            bwrap_path=path,
        )
    except OSError as exc:
        return SandboxVerdict(
            verdict="UNVERIFIABLE",
            reason=f"probe could not start: {exc}",
            backend="bubblewrap",
            bwrap_path=path,
        )
    if code == 0:
        return SandboxVerdict(
            verdict="PASS",
            reason="fixed bwrap probe exited 0",
            backend="bubblewrap",
            exit_code=0,
            bwrap_path=path,
        )
    return SandboxVerdict(
        verdict="FAIL",
        reason=f"bwrap probe exit {code}: {err}".strip(),
        backend="bubblewrap",
        exit_code=code,
        bwrap_path=path,
    )
