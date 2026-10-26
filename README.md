# Ascended Intelligence Core — TrustOS

**TrustOS: A verified governance kernel for agent actions.**

TrustOS is an open-source research and reference implementation providing an authorization, provenance, approval, correction, and auditability plane for autonomous AI agents.

**Status: As of October 2026, the core kernel is operational and fully tested.**

## Verified Implementation
- **195 tests passed**, 1 xpassed
- **80% overall code coverage**
- **Living Ledger**: Tamper-evident hash chain (`security/ledger.py`)
- **Telemetry Engine**: Live observability metrics (`security/telemetry.py`)
- **SHAPE & Delegation**: Scoped authority and fail-closed security (`security/shape.py`, `security/delegation.py`)
- **API & UI**: Gated action endpoints (`api/app.py`)

## Quick Start
```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
export AICI_API_KEY="agent-demo-key"
flask --app api.app run --host=0.0.0.0 --port=5000
```

## Edge Execution Verified
Tested and verified in Termux (Android) and Grok Sandbox, proving offline governance and telemetry can run without cloud dependency.

## Status
**NOT PRODUCTION READY.** The kernel is operational, but requires OIDC/WebAuthn and DB migrations for enterprise deployment.
