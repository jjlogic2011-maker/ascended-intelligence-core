# TrustOS Desk

Operator surface at **`/desk`** (session auth via existing UI key).

## Enable

```bash
export AICI_UI_KEY="your-ui-key"
export AICI_UI_SECRET="long-random-secret"
export AICI_API_KEY="agent-demo-key"
export AICI_APPROVER_KEY="approver-demo-key"
flask --app api.app run --host=127.0.0.1 --port=5000
```

Open `http://127.0.0.1:5000/ui/login` then `/desk`.

## What it shows

- Pending approval queue (approve/deny reuse classic UI routes)
- Process ledger tip (last events)
- TRUSTOS-RACE-001 reference status (honest non-claims)

## Non-goals

Not SSO, not multi-tenant admin, not a GRC console. Revenue path remains Pilot + Kernel Support on the governance kernel while Desk improves operator UX.
