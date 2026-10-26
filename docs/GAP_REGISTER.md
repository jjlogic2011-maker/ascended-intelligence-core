# TrustOS Gap Register

Last updated: 2026-10-26  
Rule: every gap is FIXED (with evidence), NOT_APPLICABLE (reason), or BLOCKED (dependency).

## Grade

| Current | Target next |
|---------|-------------|
| A0 achieved; A1 candidate after fail-closed harness + receipts | A1 verified on CI + local harness; then A2 OIDC |

## P0 — security / correctness

| ID | Gap | Status | Evidence / next |
|----|-----|--------|-----------------|
| P0-1 | Concurrent approve without atomic claim on live path | OPEN — integration | `claim_status` exists; approve/deny must use it (this branch wires CAS). Keep multiprocess receipt in harness. |
| P0-2 | Hard `--cov` breaking bare pytest | FIXED | pytest.ini; CI uses `-o addopts=""` |
| P0-3 | Assessment harness suppressed coverage failures | FIXED | `assessment_grade.sh` no longer uses `\|\| true` |
| P0-4 | Missing ledger file did not fail assessment | FIXED | persistence_receipt required |
| P0-5 | Credentials in logs | OPEN | Audit log statements |
| P0-6 | CSRF on HTML approve/deny | OPEN | Tokens + tests |
| P0-7 | `/execute` synthesizes approved Authorization | OPEN / scoped claim | Do not claim all routes require independent human grant; restrict claims to gated `/action` + approve path |

## P1 — design partner

| ID | Gap | Status | Next |
|----|-----|--------|------|
| P1-1 | OIDC human principal | OPEN | Flagged adapter |
| P1-2 | Durable ledger default for API process | PARTIAL | `AICI_LEDGER_PATH` honored when set |
| P1-3 | Policy version on decisions | OPEN | Ledger field |
| P1-4 | Export authenticity (signature / TSA) | OPEN | Documented: hash = integrity only |
| P1-5 | README test count vs CI | OPEN until bound to run | Prefer "see latest CI"; CI observed 197 passed |

## P2 — product / GRC

| ID | Gap | Status | Next |
|----|-----|--------|------|
| P2-1 | Agent inventory | OPEN | ROADMAP_GRC.md |
| P2-2 | Framework control library | OPEN | |
| P2-3 | SIEM export | OPEN | |
| P2-4 | SOC2 | BLOCKED | Revenue + auditor |

## A1 acceptance receipts (required)

1. Assessment CI / harness fail-closed  
2. Persistent ledger reload verify  
3. Standalone export CLI + tamper nonzero exit  
4. Concurrent claim one winner  
5. Claim consistency across README / LIMITATIONS / this register  
