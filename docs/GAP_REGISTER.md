# TrustOS Gap Register

Last updated: 2026-10-26  
Rule: every gap is FIXED (with evidence), NOT_APPLICABLE (reason), or BLOCKED (dependency).

## Grade

| Current | Target next |
|---------|-------------|
| A0–A1 (kernel operational, assessment package landing) | A2 design-partner |

## P0 — security / correctness

| ID | Gap | Status | Evidence / next |
|----|-----|--------|-----------------|
| P0-1 | Concurrent approve race without CAS | FIXED / verify on main | `claim_status` + wiring; keep race integration test |
| P0-2 | Hard `--cov` breaking bare pytest | FIXED | pytest.ini without mandatory cov in addopts |
| P0-3 | Credentials in logs | OPEN | Audit log statements; deny secrets |
| P0-4 | CSRF on HTML approve/deny | OPEN | Tokens + tests |

## P1 — design partner

| ID | Gap | Status | Next |
|----|-----|--------|------|
| P1-1 | OIDC human principal | OPEN | Flagged adapter |
| P1-2 | Durable ledger required non-dev | OPEN | Env enforcement |
| P1-3 | Policy version on decisions | OPEN | Ledger field + invalidation |
| P1-4 | Session idle / cookie flags | OPEN | Document + implement |

## P2 — product / GRC

| ID | Gap | Status | Next |
|----|-----|--------|------|
| P2-1 | Agent inventory registry | OPEN | See ROADMAP_GRC.md |
| P2-2 | Framework control library | OPEN | EU AI Act / NIST map |
| P2-3 | SIEM export | OPEN | JSON/CEF webhook |
| P2-4 | SOC2 | BLOCKED | Revenue + scope + auditor |

## Assessment harness

- Script: `scripts/assessment_grade.sh`  
- Offline export: `security.export.verify_export`  
