# TrustOS Integration Interceptor v2

**Flow**

```text
OpenAI-style Tool Request
    → Policy classification (preview available)
    → SHAPE Authorization
    → Human gate if consequential
    → GovernanceEngine
    → Living Ledger receipt
    → Evidence + compact Cardputer line
```

**Authority:** Justin James Jones  
**Status:** Reference integration layer — additive, simulated execution  
**Not:** Production GRC, multi-host consensus, live external side effects

## Gaps closed in v2

| Gap | Closure |
|-----|---------|
| No HTTP surface | Full Flask blueprint (`routes.py`) |
| No dry-run | `POST /api/tool/preview` + batch |
| No idempotency | `client_request_id` replay-safe |
| No model-turn trail | `GET /api/tool/trail/<model_request_id>` |
| No edge-friendly output | `compact` one-liner + `/api/tool/compact/<id>` |
| Deny without reason | `deny_reason` on resolve |

## API surface

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/tool/health` | public | Interceptor status |
| POST | `/api/tool/preview` | optional | Classify one tool (no side effects) |
| POST | `/api/tool/preview/batch` | optional | Classify up to 50 tools |
| POST | `/api/tool` | API key | Submit tool request |
| GET | `/api/tool/pending` | approver | List gated pending |
| POST | `/api/tool/resolve/<id>` | approver | Approve or deny |
| GET | `/api/tool/<request_id>` | optional | Fetch result |
| GET | `/api/tool/trail/<model_id>` | optional | Evidence trail for one model turn |
| GET | `/api/tool/compact/<request_id>` | optional | Cardputer one-liner |

## Wire into existing app

```python
from security.integration.routes import tool_bp, init_interceptor
init_interceptor(app, ledger=LEDGER)
app.register_blueprint(tool_bp)
```

## Still open

- Pending tool queue not yet on SQLite PendingStore (process-local)
- Real external execution still out of scope
- No production deploy of this layer

## Boundaries

Human design authority remains with Justin James Jones.  
Self-certification is insufficient.  
Not production approval, not legal advice, not regulatory compliance.
