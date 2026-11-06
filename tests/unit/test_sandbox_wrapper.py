"""Sandbox wrapper: three verdicts, no caller execution."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from security.sandbox.harness import SandboxHarness
from security.sandbox.wrapper import CONTROLS_22, build_probe_plan, probe_bubblewrap


def test_catalog_is_twenty_two():
    assert len(CONTROLS_22) == 22
    assert CONTROLS_22[0] == "deny_by_default"


def test_plan_is_fixed_true_and_no_shell():
    plan = build_probe_plan("/usr/bin/bwrap")
    assert plan.argv[0] == "/usr/bin/bwrap"
    assert plan.argv[-1] == "/bin/true"
    assert "--unshare-net" in plan.argv
    assert plan.network == "none"


def test_pass_only_on_zero(monkeypatch):
    monkeypatch.setattr("security.sandbox.wrapper.shutil.which", lambda _n: "/usr/bin/bwrap")

    def runner(_argv, _timeout):
        return 0, ""

    v = probe_bubblewrap(runner=runner)
    assert v.verdict == "PASS"
    assert v.exit_code == 0


def test_nonzero_is_fail(monkeypatch):
    monkeypatch.setattr("security.sandbox.wrapper.shutil.which", lambda _n: "/usr/bin/bwrap")

    def runner(_argv, _timeout):
        return 1, "userns denied"

    v = probe_bubblewrap(runner=runner)
    assert v.verdict == "FAIL"


def test_timeout_is_unverifiable_not_pass(monkeypatch):
    import subprocess

    monkeypatch.setattr("security.sandbox.wrapper.shutil.which", lambda _n: "/usr/bin/bwrap")

    def runner(_argv, _timeout):
        raise subprocess.TimeoutExpired(cmd=_argv, timeout=_timeout)

    v = probe_bubblewrap(runner=runner)
    assert v.verdict == "UNVERIFIABLE"
    assert v.verdict != "PASS"


def test_missing_bwrap_is_unverifiable(monkeypatch):
    monkeypatch.setattr("security.sandbox.wrapper.shutil.which", lambda _n: None)
    v = probe_bubblewrap()
    assert v.verdict == "UNVERIFIABLE"
    assert "Termux" in v.reason


def test_harness_ledger_row():
    harness = SandboxHarness()

    def runner(_argv, _timeout):
        return 0, ""

    import security.sandbox.wrapper as wrapper

    original = wrapper.shutil.which
    wrapper.shutil.which = lambda _n: "/usr/bin/bwrap"
    try:
        out = harness.run_probe(runner=runner)
    finally:
        wrapper.shutil.which = original
    assert out["verdict"] == "PASS"
    assert out["receipt_event_id"]
    ok, errors = harness.ledger.verify()
    assert ok, errors
