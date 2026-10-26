# Ascended Intelligence Core — TrustOS

**TrustOS: A verified governance kernel for agent actions.**

TrustOS is an open-source research and reference implementation providing an authorization, provenance, approval, correction, and auditability plane for autonomous AI agents.

**Status: As of October 2026, the core kernel is operational and fully tested.**

**NOT PRODUCTION READY.** Not a Fortune-50 GRC suite replacement. See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).

## Verified Implementation
- **195 tests passed**, 1 xpassed (match CI; do not inflate in marketing)
- **~80% overall code coverage**
- **Living Ledger**: Tamper-evident hash chain (`security/ledger.py`)
- **Telemetry Engine**: Ledger-backed metrics (`security/telemetry.py`)
- **SHAPE & Delegation**: Scoped authority and fail-closed security
- **Integrity Export**: Offline-verifiable receipts (`security/export.py`)
- **API & UI**: Gated action endpoints (`api/app.py`)

## Quick Start
```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
chmod +x scripts/assessment_grade.sh && ./scripts/assessment_grade.sh
export AICI_API_KEY="agent-demo-key"
flask --app api.app run --host=0.0.0.0 --port=5000
```

Offline export check:
```bash
python scripts/verify_export_cli.py path/to/receipt.json
```

## Assessment, pilot, commercial
| Doc | Purpose |
|-----|--------|
| [docs/STRATEGY_ASSESSMENT.md](docs/STRATEGY_ASSESSMENT.md) | Grades A0–A5 and sales parallel track |
| [docs/ASSESSMENT.md](docs/ASSESSMENT.md) | How to run assessment |
| [docs/GAP_REGISTER.md](docs/GAP_REGISTER.md) | P0/P1/P2 gaps |
| [docs/PILOT_RUNBOOK.md](docs/PILOT_RUNBOOK.md) | Design-partner install |
| [docs/EDGE_TERMUX.md](docs/EDGE_TERMUX.md) | Sovereign edge notes |
| [docs/ROADMAP_GRC.md](docs/ROADMAP_GRC.md) | Path toward enterprise GRC |
| [docs/SECURITY.md](docs/SECURITY.md) | Security principles |
| [commercial/](commercial/) | Pilot SOW / support drafts (counsel review) |

## Edge Execution
Tested in Termux (Android) and sandbox environments for offline-capable ledger paths. Document claims with commit SHA; see `docs/EDGE_TERMUX.md`.

## Human authority
Founder: **Justin James Jones**. Merges, production policy, and paid scope require explicit human approval.
