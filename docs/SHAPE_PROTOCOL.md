# SHAPE Protocol — Summary

SHAPE (Shared Human Approval & Policy Enforcement) defines how human authority and approval gates are applied to critical actions in TrustOS.

## Roles

- Requester: Submits an artifact or action for execution.
- Approver: Authorized human who can grant or reject specific approval gates.
- Auditor: Reviews ledger entries and approval decisions after the fact.
- Governance Admin: Configures policy rules and role assignments.

## Approval Gates

Approvals can be defined per artifact type, execution environment, or risk level. Common gates include:

- Identity Verification: ensure creator identity and credentials.
- Risk Assessment: automated risk scoring that can require manual review above thresholds.
- Purpose Review: human reviewer confirms declared purpose aligns with acceptable use.

## Typical Flow

1. Requester submits artifact and requests execution.
2. Governance Engine evaluates policy (automated checks + risk scoring).
3. If manual approval required, approver(s) receive a request with context and evidence.
4. Approver accepts or rejects; decision and rationale recorded in the Living Ledger.
5. Execution proceeds only if all required gates are approved.

## Auditing and Escalation

All SHAPE decisions are immutable entries in the Living Ledger. Escalation paths and appeal mechanisms are recorded as linked artifacts to preserve provenance.

