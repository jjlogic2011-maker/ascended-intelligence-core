# Ascended Intelligence Core — TrustOS

**TrustOS: research and reference infrastructure for trustworthy intelligence**

TrustOS is an open-source research and reference implementation exploring governance infrastructure for agentic AI.

The project focuses on preserving human authority, agent identity, authorization boundaries, provenance, evidence, auditability, and accountable execution as AI systems interact with software and external tools.

This repository intentionally distinguishes current implementation from research architecture, specifications, roadmap components, and independently validated capabilities.

---

## Current Repository State

The currently located implementation is a small Python service using Flask.

### CURRENT IMPLEMENTATION

The following components are present in source files. They are classified as CITED because no execution occurred in this audit session.

| Component | Evidence Tier | Evidence |
|---|---|---|
| API | CITED | `api/app.py` |
| Orchestrator | CITED | `core/orchestrator.py` |
| Agent Router | CITED | `agents/router.py` |
| Authentication | CITED | `security/auth.py` |
| Experts package | CITED | `experts/` |
| Unit tests | CITED | `tests/unit/` |
| Integration tests | CITED | `tests/integration/` |
| Docker configuration | CITED | `Dockerfile` |

The presence of a source file is not, by itself, proof that behavior has been successfully executed or independently validated.

### RESEARCH / ARCHITECTURE

TrustOS research architecture discusses:

- provenance and lineage;
- human authority;
- agent accountability;
- auditability;
- evidence;
- governance boundaries;
- continuity and memory concepts;
- controlled execution;
- artifact and evidence relationships.

These concepts describe the broader research direction and must not be read as proof that every described component is implemented.

### SPECIFICATION

The following located materials describe concepts without a corresponding demonstrated executable implementation in the audited repository:`

- AIRI-DNA: `docs/AIRI_DNA.md`
- broader TrustOS architecture: `docs/TRUSTOS_ARCHITECTURE.md`
- related research and design documents under `docs/`

### ROADMAP

The following are roadmap subjects in the located documentation:

- Wasmer runtime integration;
- Tenki runtime integration;
- broader runtime adapters;
- expanded TABS evaluation;
- durable evidence infrastructure;
- distributed or federated ledger concepts;
- formal verification;
- independent review and external validation.

See [`docs/ROADMAP.md`](docs/ROADMAP.md).

### NOT YET VALIDATED

The following were not independently validated in this audit:

- application startup;
- Docker build or runtime;
- complete test execution;
- coverage;
- TABS results;
- production deployment;
- security review;
- independent validation of any TrustOS capability.

The reported "42%" figure is an unverified reported figure. No denominator, raw result set, commit, or timestamp was available in the accessible repository evidence.

---

## Overview

TrustOS explores how agentic AI systems may preserve:

- **Traceability** — linking actions to available provenance and evidence;
- **Attribution** — recording declared actors and contributors;
- **Auditability** — preserving inspectable decisions and events;
- **Accountability** — associating declared responsibility with actions and outcomes.

These are specification-level objectives and architectural principles. They are not claims that every objective is currently achieved by the repository.

---

## Research Architecture and the Five Gaps

The following table preserves the project's research framing while distinguishing it from current implementation:

| Research gap | TrustOS research direction | Current evidence classification |
|---|---|---|
| Provenance loss | AIRI-DNA provenance concepts | SPECIFICATION |
| Authority drift | SHAPE human approval concepts | SPECIFICATION |
| Memory or continuity erosion | Living Ledger concepts | SPECIFICATION |
| Evidence vacuum | TABS evaluation concepts | ROADMAP |
| Accountability collapse | Controlled execution and evidence receipts | SPECIFICATION |

The classifications above describe the accessible repository state. They are not claims of completed implementation.

---

## Core Components

| Component | Research description | Current maturity |
|---|---|---|
| TrustOS Core | A proposed governance and evidence architecture | SPECIFICATION |
| SHAPE Protocol | Human authorization state machine | VERIFIED |
| Living Ledger | Proposed provenance and event-history model | SPECIFICATION |
| AIRI-DNA | Proposed deterministic provenance representation | SPECIFICATION |
| TABS | Proposed adversarial governance evaluation | ROADMAP |
| Runtime Adapters | Proposed controlled execution substrates | ROADMAP |
| Wasmer and Tenki | Future runtime integration subjects | ROADMAP |

No unsupported test count or percentage is claimed for TABS.

---

## Actual Application Architecture

The audited application uses Flask.

```text
Framework: Flask
Application object: api.app:app
Container server: Gunicorn
Container entry point: api.app:app
