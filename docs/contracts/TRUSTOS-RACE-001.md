# TRUSTOS-RACE-001 — Execution Boundary Contract

**Status:** Frozen acceptance expectations for the reference dispatcher  
**Scope:** Authority-state re-check + synthetic external effect  
**Non-claims:** Not cryptographic grant verification; not multi-database 2PC; not production finality across third-party APIs.

## Research alignment (integrations monitoring)

Industry and standards work emphasizes:

- Re-check authority at the **effect boundary** (agentic TOCTOU).
- Separate **workload identity** (who the process is) from **delegated authorization** (what it may do).
- Durable **idempotency keys** and observable sinks; ledger success ≠ external commit.
- Revocation request ≠ invalidation ≠ **revocation closure** across delayed queues.

TrustOS maps these into a **reference** kernel with a synthetic sink so tests remain falsifiable without real cloud side effects.

## Acceptance tests

| ID | Required proof |
|----|----------------|
| R01 | Revoke before dispatch → no external effect; blocked ledger event |
| R03-A | Revoke during dispatch window → no external effect; late-abort event |
| R03-B | Concurrent dispatch attempts for one request_id → at most one external effect |
| R06 | Sequential duplicate request_id → second dispatch refused |
| R06-B | After process restart with durable paths → prior request_id cannot re-effect |
| R06-C | Out-of-scope action and exhausted grant → no external effect |

## Observable oracle

`security.external_adapter.SyntheticExternalDB` is the effect oracle.  
Assertions must use `has_effect` / `get_effect`, not only ledger event types.

## Maturity

Documented + internally tested on this branch. Independent reproduction = third party runs pytest against a tagged SHA. Operational demonstration = production adapter + monitoring (not claimed).
