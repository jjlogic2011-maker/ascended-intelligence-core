# API Security Gaps + Build Decision (2026-11-06)

**Authority:** Justin James Jones  
**Status:** Decision record — not a new framework  
**Replaces:** Treating interception-as-product as the primary build goal

## 1. Honest framing

Intercept tool calls and emit receipts is **table stakes**. HELM AI Kernel, Microsoft Agent Governance Toolkit, MCP security gateways, and commercial agent gateways already ship this pattern. TrustOS must not position itself as a ninth interception product.

This branch adds an **adapter** that routes OpenAI-style tool shapes through the existing TrustOS kernel (SHAPE, human gates, Living Ledger). It is complementary infrastructure, not the innovation thesis.

## 2. Missing API security features (research-backed)

Compared to OWASP Agentic Top 10 (ASI02/ASI03), MCP gateway guidance, and HELM/AGT patterns, the current TrustOS API + this interceptor are **missing**:

| # | Missing feature | Why it matters | Priority |
|---|-----------------|----------------|----------|
| 1 | **Per-tool privilege profiles** (scopes, rate limits, egress allowlists) | OWASP ASI02: privilege belongs to the tool call, not only the agent | P0 |
| 2 | **Argument schema validation** outside the model | Prevents out-of-policy amounts / paths while tool name is allowed | P0 |
| 3 | **Named human approver on the capability grant** (not only on the call) | Corpus Gap 1; every system gates the call; few gate the grant | P0 (thesis) |
| 4 | **Fail-closed when policy service is down** | Agent gateway requirement: outage must not open the door | P0 |
| 5 | **No token passthrough / no upstream keys in agent** | MCP security: credentials held by gateway | P1 |
| 6 | **Tool definition pinning / change control** | Detect poisoned or drifted tool schemas before dispatch | P1 |
| 7 | **Three-verdict receipts: PASS / FAIL / UNVERIFIABLE** | Corpus rule; timeout must never become pass | P0 (thesis) |
| 8 | **Trajectory scoring** (sequence of tool calls, not final response) | Corpus Gap 2 | P1 (thesis) |
| 9 | **Correction propagation with machine-verifiable closure** | Corpus Gap 3 | P1 (thesis) |
| 10 | **Signed offline-verifiable receipts** (beyond local hash chain) | HELM EvidencePack pattern | P1 |
| 11 | **PendingStore-backed tool queue** (not process-local) | Survive restart; match existing /action path | P0 for production path |
| 12 | **Rate / token budgets per agent and per tool** | Denial-of-wallet / unbounded consumption | P1 |
| 13 | **Identity propagation** (agent + human principal pair on every decision) | Required for audit and grant attribution | P0 |
| 14 | **Response-side scanning** (PII/secret in tool returns) | MCP gateway post-tool stage | P2 |

What this interceptor **already has**: consequential classification, SHAPE states, human gate for gated actions, Living Ledger append, idempotency key, model-turn trail, policy preview, compact Cardputer line.

## 3. Integration with corpus synthesis (four gaps)

Do **not** expand interception as the product. Prioritize:

1. **Gap 1 — Named approver on the grant**  
   Extend AuthorityGrant / approval issuance so a human identity is bound when a capability is granted, not only when a call is approved.

2. **Gap 2 — Trajectory evaluation**  
   Score sequences of tool decisions under one model_request_id (partially enabled by /api/tool/trail).

3. **Gap 3 — Correction closure**  
   Separate track; falsification harness first (closed: false must be possible).

4. **Gap 4 — Ratified binding spec**  
   One short profile that binds SHAPE + Ledger + grants + three-verdict rule — not 22 new frameworks.

## 4. EN 18286:2026 (Article 17 QMS)

Verified: first harmonised standard under the EU AI Act for quality management (Article 17). Presumption of conformity is **narrow** (only the Article 17 requirements the standard covers). Application dates for high-risk obligations remain 2027/2028 depending on annex.

**Use:** Map existing TrustOS tracks (authority, evidence, ledger, TABS) into a **QMS evidence packet** — not a claim of conformity. Synthetic data only until independent assessment.

Recommended first artifacts (product path MetaSupers QMS Evidence Mapper v0.1):
- article17_control_register.json
- trustos_22_track_crosswalk.csv
- qms_evidence_record.schema.json
- Synthetic TABS cases for missing evidence / unapproved changes

## 5. Substrate note

HELM AI Kernel (Apache-2.0) is a real, runnable fail-closed boundary with signed receipts and a public tamper demo. Microsoft AGT similarly documents pre-execution policy. Prefer **profile + four gaps** over re-implementing interception.

## 6. Next single action for this branch

1. Open PR for feature/tool-interceptor-v2.
2. Run pytest on the unit tests against the real kernel.
3. Do **not** claim production readiness.
4. Parallel track: one hour HELM tamper demo or git log + pytest -q paste for kernel verification (corpus execution gate).

## Boundaries

Not production approval. Not legal conformity. Not a certificate.  
Human design authority remains with Justin James Jones.  
Self-certification is insufficient.
