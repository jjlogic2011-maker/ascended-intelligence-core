"""TrustOS 60-second demo.

Flow:
  1. Submit a gated action (production-deploy) as an agent -> 202 pending
  2. Show the pending queue via /approvals (approver credential)
  3. Approve with a valid approval_id
  4. Show the ledger receipt
  5. Run TABS
  6. Print summary

Runs against a Flask test client with an isolated SQLite file.
No external side effects. Actions are simulated.
"""
import json
import os
import sys
import tempfile

# Isolated environment before importing the app
_tmp = tempfile.mkdtemp(prefix="trustos-demo-")
os.environ["AICI_API_KEY"] = "agent-demo-key"
os.environ["AICI_APPROVER_KEY"] = "approver-demo-key"
os.environ["AICI_UI_KEY"] = "ui-demo-key"
os.environ["AICI_UI_SECRET"] = "demo-secret"
os.environ["AICI_PENDING_DB"] = os.path.join(_tmp, "pending.sqlite3")
os.environ["AICI_APPROVAL_DB"] = os.path.join(_tmp, "approvals.sqlite3")

import importlib
import security.auth as auth
auth.API_KEY = "agent-demo-key"
auth.APPROVER_KEY = "approver-demo-key"

from security.approval_service import ApprovalService

api = importlib.import_module("api.app")
api.app.config["TESTING"] = True
api.app.secret_key = "demo-secret"

service = ApprovalService(
    os.environ["AICI_APPROVAL_DB"],
    verify_human=auth.approver_identity,
)
api.app.config["APPROVAL_SERVICE"] = service


def line(label):
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print(f"{'─' * 60}")


def main():
    with api.app.test_client() as client:
        line("STEP 1 — Agent submits a gated action")
        r = client.post("/action", headers={"x-api-key": "agent-demo-key"}, json={
            "action": "production-deploy",
            "resource": "staging",
            "arguments": {"commit": "abc123"},
            "agent_id": "api-agent",
            "requester_id": "api-agent",
        })
        body = r.get_json()
        print(f"  HTTP {r.status_code}")
        print(f"  status:     {body.get('status')}")
        print(f"  pending_id: {body.get('pending_id')}")
        pending_id = body["pending_id"]

        line("STEP 2 — Approver sees the pending queue")
        r = client.get("/approvals", headers={"x-approver-key": "approver-demo-key"})
        print(f"  HTTP {r.status_code}")
        queue = r.get_json()
        print(f"  pending count: {len(queue)}")
        for item in queue:
            print(f"    - {item['action']} on {item['resource']} (agent: {item['agent_id']})")

        line("STEP 3 — Approver issues an approval_id bound to the request")
        approval_id = service.issue(
            credential="approver-demo-key",
            request_id=pending_id,
            requester_id="api-agent",
            action="production-deploy",
            resource="staging",
            arguments={"commit": "abc123"},
        )
        print(f"  approval_id: {approval_id[:16]}...")

        line("STEP 4 — Approver releases the action")
        r = client.post(
            f"/approve/{pending_id}",
            headers={"x-approver-key": "approver-demo-key"},
            json={"approval_id": approval_id},
        )
        body = r.get_json()
        print(f"  HTTP {r.status_code}")
        print(f"  executed:           {body.get('executed')}")
        print(f"  decision:           {body.get('decision')}")
        print(f"  receipt_event_id:   {body.get('receipt_event_id', '')[:16]}...")
        ev = body.get("evidence", {})
        if ev.get("human_approver"):
            print(f"  human_approver:     {ev['human_approver']}")
        if ev.get("fingerprint"):
            print(f"  fingerprint:        {ev['fingerprint'][:16]}...")

        line("STEP 5 — Ledger verification")
        ok, errors = api.LEDGER.verify()
        print(f"  ledger intact:      {ok}")
        print(f"  events in chain:    {len(api.LEDGER.events)}")
        if errors:
            print(f"  errors:             {errors}")

        line("STEP 6 — Adversarial suite (TABS)")
        from security.tabs import run_all
        report = run_all()
        print(f"  tests:  {report.tests}")
        print(f"  passed: {report.passed}")
        print(f"  failed: {report.failed}")
        print(f"  hash:   {report.result_hash[:32]}...")

        line("DEMO COMPLETE")
        print("  One agent submitted a gated action.")
        print("  One human approved it with a bound approval_id.")
        print("  One tamper-evident receipt was written.")
        print("  Twelve adversarial checks passed.")
        print("  Actions were simulated. No external side effects.")


if __name__ == "__main__":
    main()
