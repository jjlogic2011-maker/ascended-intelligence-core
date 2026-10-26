# TrustOS Limitations (binding)

**Authority:** Justin James Jones, Founder — Ascended Intelligence  
**Status:** Binding for all public claims, pilots, and support SKUs.

## What this is

- An open-source **reference governance kernel** for agent actions: authorization, pending approval, fail-closed paths, Living Ledger, integrity export, basic telemetry.
- A **working, tested** implementation suitable for research, design partners, and embed evaluation.

## What this is NOT

- **Not production-ready** for Fortune-50 multi-tenant SaaS without further engineering and assurance.
- **Not** a full GRC suite (no complete AI inventory, intake committees, multi-framework residual risk workspace comparable to Credo AI / OneTrust AI / IBM watsonx.governance as of this document).
- **Not** AGI, consciousness, medical, or therapeutic software.
- **Not** a certified zero-trust network product (ZTNA). Design is zero-trust-*oriented* (fail-closed grants, evidence).
- **Not** SOC 2 / ISO 27001 certified unless an independent report is linked here.

## Technical boundaries

| Area | Current state |
|------|----------------|
| Identity | Shared API keys / early adapters; full OIDC + SCIM is roadmap |
| Storage | Local ledger / SQLite patterns; not claimed multi-region HA |
| Dispatch | Simulated by default; live adapters require explicit allowlist + human policy |
| UI security | CSRF and session hardening are explicit work items |
| Scale | Reference-scale; not benchmarked for 10k+ agents |

## Allowed claims

- Tests pass as reported by CI / `scripts/assessment_grade.sh`.
- Living Ledger is append-only and tamper-*evident* (hash chain).
- Integrity export can be verified offline with `verify_export`.
- Fail-closed authorization when grants are missing/invalid (kernel paths).

## Forbidden claims (until evidenced)

- “Replaces OneTrust / Credo / IBM for enterprise GRC.”
- “Production certified” / “audit-ready for any regulator without mapping work.”
- Exact test counts that disagree with README/CI.

## Human authority

Merge to `main`, production deploy, paid scope changes, and external disclosures require **Justin James Jones** approval.
