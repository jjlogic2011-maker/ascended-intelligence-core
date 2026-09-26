"""TABS — TrustOS Assurance & Benchmark Suite.

Twelve adversarial checks against the governance loop. Each check
exercises a specific failure mode. The runner computes a SHA-256
result hash over the deterministic result payload. It never hardcodes
success. Exit code is non-zero when any check fails.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from typing import Callable

from security.airi_dna import build_dna, fingerprint_content
from security.governance import (
    AgentIdentity,
    GovernanceEngine,
    GovernanceRequest,
)
from security.ledger import LedgerEvent, LivingLedger, load_ledger
from security.shape import Authorization, ShapeError, State

NOT_AVAILABLE = "NOT_AVAILABLE"


def _try_git_commit() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return out.decode("utf-8").strip()
    except Exception:
        return NOT_AVAILABLE


@dataclass
class TabsResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class TabsReport:
    tests: int
    passed: int
    failed: int
    timestamp: str
    commit: str
    result_hash: str
    results: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tests": self.tests,
            "passed": self.passed,
            "failed": self.failed,
            "timestamp": self.timestamp,
            "commit": self.commit,
            "result_hash": self.result_hash,
            "results": [
                {"name": r.name, "passed": r.passed, "detail": r.detail}
                for r in self.results
            ],
        }


def _base_engine():
    ledger = LivingLedger()
    agents = {
        "agent-ok": AgentIdentity("agent-ok", frozenset({"read", "write"})),
        "agent-narrow": AgentIdentity("agent-narrow", frozenset({"read"})),
        "agent-revoked": AgentIdentity(
            "agent-revoked", frozenset({"read", "write"}), revoked=True
        ),
    }
    policies = {"read": {"read"}, "write": {"write"}}
    return GovernanceEngine(ledger=ledger, agents=agents, policies=policies), ledger


def _approved():
    a = Authorization(request_id="req")
    a.transition(State.ASSESSED, actor="system")
    a.transition(State.APPROVED, actor="human")
    return a


def _req(agent_id="agent-ok", action="write", request_id="req-1"):
    return GovernanceRequest(
        request_id=request_id,
        agent_id=agent_id,
        action=action,
        artifact_id="art-1",
        artifact_content=b"hello",
        creator="creator-1",
        version="1.0.0",
        provenance={"source": "tabs"},
    )


def tabs_001_unauthorized_action() -> bool:
    engine, _ = _base_engine()
    auth = Authorization(request_id="req")
    res = engine.process(_req(), authorization=auth)
    return res.executed is False


def tabs_002_expired_authorization() -> bool:
    engine, _ = _base_engine()
    auth = _approved()
    auth.expires_at = time.time() - 10
    res = engine.process(_req(), authorization=auth)
    return res.executed is False


def tabs_003_revoked_agent() -> bool:
    engine, _ = _base_engine()
    res = engine.process(_req(agent_id="agent-revoked"), authorization=_approved())
    return res.executed is False


def tabs_004_authority_escalation() -> bool:
    engine, _ = _base_engine()
    res = engine.process(
        _req(agent_id="agent-narrow", action="write"), authorization=_approved()
    )
    return res.executed is False


def tabs_005_replayed_request() -> bool:
    engine, _ = _base_engine()
    auth = _approved()
    r = _req()
    first = engine.process(r, authorization=auth)
    second = engine.process(r, authorization=auth)
    return first.executed is True and second.executed is False


def tabs_006_modified_receipt() -> bool:
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "ledger.jsonl")
        ledger = LivingLedger(path=path)
        ledger.append(
            event_type="EXECUTED", actor="a", agent="ag",
            request_id="r", artifact_id="art",
        )
        with open(path, "r", encoding="utf-8") as fh:
            data = json.loads(fh.readline())
        data["artifact_id"] = "art-tampered"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n")
        loaded = load_ledger(path)
        ok, errors = loaded.verify()
        return (not ok) and any("event_hash" in e for e in errors)


def tabs_007_missing_provenance() -> bool:
    try:
        build_dna(
            artifact_id="a", creator="c", version="1",
            timestamp="2026-01-01T00:00:00Z",
            provenance=None, content=b"x",
        )
        return False
    except ValueError:
        return True


def tabs_008_altered_artifact() -> bool:
    return fingerprint_content(b"original") != fingerprint_content(b"altered")


def tabs_009_policy_bypass() -> bool:
    engine, _ = _base_engine()
    engine.policies = {}
    res = engine.process(_req(action="write"), authorization=_approved())
    return res.executed is False


def tabs_010_invalid_agent_identity() -> bool:
    engine, _ = _base_engine()
    res = engine.process(_req(agent_id="ghost"), authorization=_approved())
    return res.executed is False


def tabs_011_external_tool_without_approval() -> bool:
    engine, _ = _base_engine()
    engine.policies["external-tool"] = {"external"}
    res = engine.process(
        _req(action="external-tool"), authorization=_approved()
    )
    return res.executed is False


def tabs_012_malformed_evidence_bundle() -> bool:
    try:
        Authorization()  # type: ignore[call-arg]
        return False
    except TypeError:
        return True


_CHECKS = [
    ("TABS-001", tabs_001_unauthorized_action),
    ("TABS-002", tabs_002_expired_authorization),
    ("TABS-003", tabs_003_revoked_agent),
    ("TABS-004", tabs_004_authority_escalation),
    ("TABS-005", tabs_005_replayed_request),
    ("TABS-006", tabs_006_modified_receipt),
    ("TABS-007", tabs_007_missing_provenance),
    ("TABS-008", tabs_008_altered_artifact),
    ("TABS-009", tabs_009_policy_bypass),
    ("TABS-010", tabs_010_invalid_agent_identity),
    ("TABS-011", tabs_011_external_tool_without_approval),
    ("TABS-012", tabs_012_malformed_evidence_bundle),
]


def run_all() -> TabsReport:
    results = []
    for name, fn in _CHECKS:
        try:
            passed = bool(fn())
            detail = ""
        except Exception as e:
            passed = False
            detail = f"{type(e).__name__}: {e}"
        results.append(TabsResult(name=name, passed=passed, detail=detail))

    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    commit = _try_git_commit()

    payload = {
        "tests": len(results),
        "passed": passed_count,
        "failed": failed_count,
        "timestamp": ts,
        "commit": commit,
        "results": [{"name": r.name, "passed": r.passed} for r in results],
    }
    result_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return TabsReport(
        tests=len(results),
        passed=passed_count,
        failed=failed_count,
        timestamp=ts,
        commit=commit,
        result_hash=result_hash,
        results=results,
    )


if __name__ == "__main__":
    report = run_all()
    print(json.dumps(report.to_dict(), indent=2))
    raise SystemExit(1 if report.failed else 0)
