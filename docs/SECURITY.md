# Security

## Principles

1. **Fail-closed** — no valid grant → no execution (kernel paths).  
2. **Evidence** — consequential decisions append to Living Ledger.  
3. **Least privilege** — delegation narrows; no silent escalation.  
4. **Human authority** — production policy changes require Justin James Jones.  

## Reporting

Responsible disclosure: open a private security advisory on GitHub or email the maintainer channel listed in pilot contracts. Do not file public issues with exploit details.

## Secrets

- Never commit API keys, OIDC client secrets, or customer ledger data.  
- Rotate demo keys in any shared environment.  

## Dependencies

- Prefer pinned requirements in release tags.  
- CI should surface known vulnerable packages when tooling is available.  

## Known residual risks (see GAP_REGISTER)

- CSRF on browser forms until closed  
- Shared-key identity until OIDC  
- Single-node ledger durability defaults  
