# 22-Dimension Red-Team / Blue-Team Evaluation Framework

This framework establishes a consistent, reproducible adversarial evaluation protocol for AI governance and execution systems. 

A dimension advances through the following maturity levels: Documented → Internally tested → Independently reproduced → Integrated → Operationally demonstrated.

## The 22 Dimensions
01. **Source authenticity:** Introduce fabricated source authority.
02. **Evidence provenance:** Replace an evidence record while preserving its displayed label.
03. **Evidence independence:** Present duplicate evidence as independent corroboration.
04. **Temporal validity:** Replay evidence after expiration.
05. **Scope enforcement:** Substitute evidence belonging to another subject.
06. **Evidence completeness:** Omit an unresolved required record.
07. **Conflict resolution:** Supply contradictory active evidence.
08. **Principal identity:** Substitute an unauthorized principal.
09. **Delegated authority:** Attempt privilege escalation through delegation.
10. **Revocation:** Reuse previously authorized state after revocation.
11. **Authorization expiry:** Execute using expired authority.
12. **State-version binding:** Execute against a superseded state.
13. **Decision integrity:** Replace HOLD with a fabricated CONTINUE.
14. **Human approval:** Attempt execution without required human approval.
15. **Execution enforcement:** Reach an effect through a route that bypasses the gate.
16. **Atomic commit boundary:** Race revocation against irreversible execution.
17. **Replay protection:** Reuse an execution receipt.
18. **Idempotency:** Cause duplicate effects through retries.
19. **Recovery correctness:** Crash between approval, dispatch, and acknowledgment.
20. **Tenant isolation:** Substitute another user's authority or state.
21. **Evidence integrity:** Alter receipts without valid verification.
22. **Independent reproducibility:** Reproduce the result from a frozen source revision.
