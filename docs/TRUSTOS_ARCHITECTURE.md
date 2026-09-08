# TRUSTOS Architecture

This document provides a high-level overview of TrustOS architecture, its core services, and how data flows between components. It is intended as a living summary; refer to implementation files and the Living Ledger for exact schemas and interfaces.

## High-level Components

- TrustOS Core API: REST/HTTP API (FastAPI) exposing artifact creation, query, and governance endpoints.
- Artifact Registry: stores artifact metadata and versioning information; interfaces with the Living Ledger for immutability guarantees.
- Evidence Vault: secure store for test results, execution receipts, and audit logs.
- Governance Engine: enforces SHAPE protocol policies, approval gates, and role-based controls.
- Runtime Adapters: sandboxed execution environments (Wasmer, Tenki, containers) that produce verifiable execution receipts.
- TABS Runner: adversarial test harness that produces structured evaluations for artifacts and agents.

## Data Flow

1. Agent or user submits an artifact via the Core API.
2. Artifact metadata is recorded in the Artifact Registry and a Living Ledger entry is created (content hash, lineage, creator).
3. If execution is requested, the Governance Engine determines required approvals (SHAPE) and dispatches code to a Runtime Adapter.
4. Runtime Adapter executes in a sandbox, emits an execution receipt, and stores artifacts/evidence in the Evidence Vault.
5. TABS suite runs adversarial tests against the artifact or agent; results are stored and linked to the Living Ledger entry.
6. Auditors can query the Core API to retrieve artifact lineage, evidence, and fingerprints (AIRI-DNA) for inspection.

## Deployment Notes

- Services are designed to be modular and deployable as containers. Use the Living Ledger schema to ensure compatibility across versions.
- Runtime Adapters must be isolated and produce signed receipts to ensure verifiability.

