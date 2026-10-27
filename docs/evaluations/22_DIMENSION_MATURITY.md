# 22-Dimension Maturity Snapshot (reference kernel)

Levels: **D** Documented · **T** Internally tested · **R** Independently reproduced · **I** Integrated · **O** Operationally demonstrated

Honest default: most dimensions are **D/T** only. Do not claim R/I/O without external evidence.

| # | Dimension | Level | Notes |
|---|-----------|-------|--------|
| 01 | Source authenticity | D | Fabricated authority sources not fully red-teamed |
| 02 | Evidence provenance | T | Ledger + export integrity tests |
| 03 | Evidence independence | D | |
| 04 | Temporal validity | T | Grant expiry paths |
| 05 | Scope enforcement | T | `permits` + DISPATCH_BLOCKED_SCOPE |
| 06 | Evidence completeness | D | |
| 07 | Conflict resolution | D | |
| 08 | Principal identity | D/T | Shared keys; OIDC not done |
| 09 | Delegated authority | T | Delegation module + grants |
| 10 | Revocation | T | R01 / R03-A |
| 11 | Authorization expiry | T | `is_expired` |
| 12 | State-version binding | D | |
| 13 | Decision integrity | D/T | |
| 14 | Human approval | T | Gated action API tests |
| 15 | Execution enforcement | T | Dispatcher boundary (reference) |
| 16 | Atomic commit boundary | T | R03-A vs synthetic sink; not distributed atomic |
| 17 | Replay protection | T | request_id + durable processed optional |
| 18 | Idempotency | T | In-memory + optional durable; not multi-host cluster |
| 19 | Recovery correctness | D/T | R06-B restart path |
| 20 | Tenant isolation | D | |
| 21 | Evidence integrity | T | Export hash verify |
| 22 | Independent reproducibility | D | Needs external party run of frozen SHA |

**Capability engine rule:** advance a dimension only one step when evidence exists; ×22 means score all rows, never invent O.
