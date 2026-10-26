# Ascended Intelligence Core — TrustOS

**TrustOS: A verified governance kernel for agent actions.**

TrustOS is an open-source research and reference implementation providing an authorization, provenance, approval, correction, and auditability plane for autonomous AI agents.

**Status: As of October 2026, the core kernel is operational and tested.**

**NOT PRODUCTION READY.** Not a Fortune-50 GRC suite. See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).

## Verified Implementation

Prefer **latest green CI** over static numbers in this file.

- CI baseline (example run on main): **197 passed**, 1 xpassed, **~80%** coverage on workflow-selected modules — always re-check Actions.
- **Living Ledger**: Tamper-evident hash chain (`security/ledger.py`)
- **Telemetry**: Ledger-backed metrics (`security/telemetry.py`)
- **SHAPE & Delegation**: Scoped authority; fail-closed on tested gated paths
- **Integrity Export**: Offline packet integrity (`security/export.py`) — not issuer authenticity
- **PendingStore.claim_status**: CAS claim for concurrent workers sharing one DB file

## Quick Start

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q -o addopts=""
chmod +x scripts/assessment_grade.sh && ./scripts/assessment_grade.sh
export AICI_API_KEY="agent-demo-key"
export AICI_LEDGER_PATH="$(pwd)/artifacts/ledger.jsonl"
flask --app api.app run --host=0.0.0.0 --port=5000
```

```bash
python scripts/verify_export_cli.py path/to/receipt.json
```

## Assessment, pilot, commercial

| Doc | Purpose |
|-----|--------|
| [docs/STRATEGY_ASSESSMENT.md](docs/STRATEGY_ASSESSMENT.md) | Grades A0–A5 |
| [docs/ASSESSMENT.md](docs/ASSESSMENT.md) | Fail-closed harness |
| [docs/GAP_REGISTER.md](docs/GAP_REGISTER.md) | P0/P1/P2 |
| [docs/PILOT_RUNBOOK.md](docs/PILOT_RUNBOOK.md) | Design-partner install |
| [docs/EDGE_TERMUX.md](docs/EDGE_TERMUX.md) | Edge notes |
| [docs/ROADMAP_GRC.md](docs/ROADMAP_GRC.md) | Enterprise GRC path |
| [docs/SECURITY.md](docs/SECURITY.md) | Security principles |
| [commercial/](commercial/) | Draft SOW/MSA — counsel review |

## Human authority

Founder: **Justin James Jones**. Merges, production policy, and paid scope require explicit human approval.
