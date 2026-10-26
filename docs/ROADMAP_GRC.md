# Roadmap: Fortune-50 class GRC + runtime (vs Credo / OneTrust / IBM)

**End-state:** Agentic GRC **plus** runtime authorization and cryptographic evidence—not inventory-only questionnaires.

## Capability matrix

| Domain | Enterprise expectation | TrustOS now | Target |
|--------|------------------------|-------------|--------|
| Inventory | Agents, models, tools, owners | Minimal | Full registry |
| Intake / workflow | Use-case forms, committees | Action gates only | Intake + action |
| Policy library | EU AI Act, NIST RMF, ISO 42001 | Kernel policies | Mapped controls |
| Risk | Inherent / residual | Minimal | Scored residual |
| Runtime enforce | Block / approve / log | **Strength** | Scale + multi-host |
| Evidence | Auditor packs | **Ledger + export** | Retention, legal hold |
| Identity | SSO, SCIM, agent IDs | Early | OIDC + SCIM + workload ID |
| Integrations | IdP, SIEM, ITSM | Thin | Priority connectors |
| Assurance | SOC2, ISO 27001 | None | When revenue funds |

## Phases

| Phase | Grade | Focus |
|-------|-------|--------|
| 0–3 mo | A1→A2 | Assessment harness, CSRF, OIDC flag, pilot packaging |
| 3–9 mo | A3 | Durable store, SIEM, admin, retention |
| 9–18 mo | A4 | Inventory, workflows, control library |
| 18–36 mo | A5 | Scale, certs, SI channel |

## Non-goals until evidenced

- Claiming GRC feature parity with named vendors  
- Shipping untested multi-tenant billing  

## Source of truth

Gaps tracked in `docs/GAP_REGISTER.md`. Kernel must not regress while GRC epics land on separate PRs.
