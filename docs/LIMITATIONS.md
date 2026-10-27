# TrustOS Limitations (binding)

**Authority:** Justin James Jones  

## What this is
Reference governance kernel: gates, ledger, export, dispatcher boundary (TRUSTOS-RACE-001), optional Desk UI.

## What this is not
Not production Fortune-50 GRC. Not cryptographic grant verification. Not multi-host 2PC finality. Not SOC2 unless independently reported.

## Integrity export
`export_hash` proves packet consistency, not independent issuer authenticity.

## Approval concurrency
Prefer `PendingStore.claim_status` on approve/deny paths (CAS). Process-local locks alone are not a distributed guarantee.
