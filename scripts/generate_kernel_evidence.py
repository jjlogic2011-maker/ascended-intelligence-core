"""Generate a kernel verification evidence bundle.

Runs the actual test suite and TABS, captures results, writes a JSON
artifact. Nothing is fabricated. Every value is derived from execution
or marked NOT_AVAILABLE with a reason.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time


def run(cmd):
    try:
        out = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, timeout=300
        ).decode("utf-8", errors="replace")
        return out
    except subprocess.CalledProcessError as e:
        return e.output.decode("utf-8", errors="replace")
    except Exception as e:
        return f"NOT_AVAILABLE: {type(e).__name__}: {e}"


def main():
    commit = run(["git", "rev-parse", "HEAD"]).strip() or "NOT_AVAILABLE"

    pytest_out = run([sys.executable, "-m", "pytest", "-q"])
    pytest_last = pytest_out.strip().splitlines()[-1] if pytest_out.strip() else "NOT_AVAILABLE"

    tabs_out = run([sys.executable, "-m", "security.tabs"])
    try:
        tabs_json = json.loads(tabs_out)
    except Exception:
        tabs_json = {"raw": tabs_out, "parse": "FAILED"}

    coverage_out = run([sys.executable, "-m", "coverage", "report"])

    bundle = {
        "schema_version": "1.0",
        "artifact_type": "kernel-verification",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": commit,
        "environment": {
            "python_version": sys.version,
            "platform": platform.platform(),
        },
        "pytest": {
            "summary_line": pytest_last,
            "raw_output_tail": "\n".join(pytest_out.strip().splitlines()[-5:]),
        },
        "tabs": tabs_json,
        "coverage": {
            "raw_output": coverage_out,
        },
        "verification_commands": [
            "pytest -q",
            "python -m security.tabs",
            "coverage run -m pytest -q && coverage report",
        ],
    }

    canonical = json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode("utf-8")
    bundle["bundle_hash"] = hashlib.sha256(canonical).hexdigest()

    path = "evidence/kernel-verification-2026-09-25.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(bundle, fh, indent=2, sort_keys=True)

    print(f"Wrote {path}")
    print(f"commit: {commit}")
    print(f"pytest: {pytest_last}")
    print(f"tabs: {tabs_json.get('passed', '?')}/{tabs_json.get('tests', '?')}")
    print(f"bundle_hash: {bundle['bundle_hash'][:16]}...")


if __name__ == "__main__":
    main()
