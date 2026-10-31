# Ascended Intelligence Core — TrustOS

**TrustOS: a reference governance kernel for agent actions.**

TrustOS is an open-source research implementation of authorization, provenance, human approval, and auditability for agent actions. It is not a production GRC product.

**Verified commit:** `7238556c3c93cd10ee3c892dbd27da165db95834` (2026-10-31).

## What was run

Python 3.11.2, jsonschema 4.26.0, pytest 9.2.0, in an isolated environment against that commit:

- **476 passed, 1 xpassed**
- **83% coverage** (1459 statements, 254 missed). `security/tabs.py` is included and is 0%.
- **TABS 12/12**

GitHub Actions baseline uses Python 3.11. Python 3.10.22 cannot collect the schema parsers (`typing.NotRequired`). This commit was not re-run on Termux.

## What the code does

- Living Ledger: hash chain in `security/ledger.py`
- Telemetry in `security/telemetry.py`
- SHAPE and delegation in `security/shape.py` and `security/delegation.py`
- Approve, deny, and malformed close call `PendingStore.claim_status`
- `ExecutionDispatcher` re-checks an in-memory grant before a synthetic file effect. `POST /approve` does not call it.
- JSON Schema parsers for an authority request, a claim record, a witness event, and a memory beacon. Parsing a record does not create a SHAPE grant.

## What is not claimed

- Not production. Not SOC 2.
- Shared API and approver keys. No OIDC or WebAuthn.
- Not cryptographic grant verification.
- Not multi-host atomic finality. Inserting a request still uses a process-local lock.
- The 22-dimension matrix has no Operational (O) score.
- A separate-process test proves `PendingStore.claim_status` lets one writer win. It does not prove the HTTP server is multi-host safe.

## Quick start

Requires Python 3.11 or newer.

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
export AICI_API_KEY="agent-demo-key"
export AICI_APPROVER_KEY="approver-demo-key"
flask --app api.app run --host=0.0.0.0 --port=5000
```

`AICI_APPROVER_KEY` must be different from `AICI_API_KEY`. If they match, approver login fails closed.
