# Advancement plan (post PR #29)

## Verified foundation

- TRUSTOS-RACE-001 on main (`2cfa572`): synthetic external sink, late authority-state re-check, durable idempotency option, 22-dim maturity snapshot.
- Existing `/ui` approval HTML + API gates.

## Near-term product (revenue-aligned)

| Priority | Item | Why |
|----------|------|-----|
| P0 | TrustOS Desk `/desk` | Sellable demo surface for pilots |
| P0 | Wire Desk into `api.app` | One process, one port |
| P1 | CSRF on UI forms | Design-partner hygiene |
| P1 | OIDC human principal | Replace shared UI key |
| P1 | Export button on Desk | Offline integrity pack for buyers |
| P2 | Dispatcher metrics on Desk | Race/block counts from ledger |
| P2 | Durable ledger path default | Match edge story |

## Sophisticated features (anticipate, do not overclaim)

1. **Effect adapters** — replace synthetic DB with allowlisted HTTP/tool adapters + per-adapter idempotency store.
2. **Grant crypto (optional)** — signed AuthorityGrant; verify at boundary (separate from state flags).
3. **SPIFFE/workload ID** — authenticate agent process; still separate from human delegation.
4. **Revocation closure receipts** — track in-flight work after revoke (standards direction).
5. **Connected tools** — GitHub Actions evidence links, Notion pilot runbooks, scheduled Automations for repo health.

## Revenue packaging (unchanged honesty)

- Community OSS
- Fixed-scope Pilot (Desk + one gated path + export)
- Kernel Support annual

Do not sell Fortune-50 GRC replacement until inventory/workflows/assurance exist.
