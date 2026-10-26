# TrustOS Limitations (binding)

**Authority:** Justin James Jones, Founder — Ascended Intelligence  
**Status:** Binding for all public claims, pilots, and support SKUs.

## What this is

- An open-source **reference governance kernel** for agent actions: authorization, pending approval, fail-closed paths, Living Ledger, integrity export, basic telemetry.
- A **working, tested** implementation suitable for research, design partners, and embed evaluation.

## What this is NOT

- **Not production-ready** for Fortune-50 multi-tenant SaaS without further engineering and assurance.
- **Not** a full GRC suite comparable to Credo AI / OneTrust AI / IBM watsonx.governance.
- **Not** AGI, consciousness, medical, or therapeutic software.
- **Not** a certified ZTNA product. Design is zero-trust-*oriented*.
- **Not** SOC 2 / ISO 27001 certified unless an independent report is linked here.

## Integrity export vs authenticity

| Capability | Status |
|------------|--------|
| Offline **consistency** of an export packet (SHA-256 over canonical JSON) | Implemented (`verify_export` / CLI) |
| **Independent authenticity** (who issued the packet: signature, TSA, external anchor) | **Not implemented** — do not promise this in pilots |

Anyone who can rewrite the packet can recompute `export_hash`. Treat export as tamper-evident relative to the hash, not as non-repudiable third-party proof.

## Technical boundaries

| Area | Current state |
|------|----------------|
| Identity | Shared API keys / early adapters; OIDC roadmap |
| Gated `/action` + approve | Human approval path with pending store |
| `/execute` | May construct internal authorization for legacy orchestrator — **do not** claim this route requires independent human grant |
| Storage | `AICI_LEDGER_PATH` enables on-disk ledger; default process may be in-memory |
| Dispatch | Simulated by default |
| Concurrent claims | `PendingStore.claim_status` CAS; live HTTP path must use it |

## Allowed claims

- Tests pass as reported by CI / fail-closed `scripts/assessment_grade.sh`.
- Living Ledger is append-only and tamper-*evident* (hash chain).
- Integrity export verifies offline for **packet integrity**.
- Fail-closed authorization on **tested gated paths** when grants are missing/invalid.

## Forbidden claims (until evidenced)

- “Replaces OneTrust / Credo / IBM.”
- “Production certified” / universal regulator readiness.
- “Cryptographically proves issuer identity” via export hash alone.
- Exact test counts that disagree with the cited CI run.

## Human authority

Merge to `main`, production deploy, paid scope changes, and external disclosures require **Justin James Jones** approval.
