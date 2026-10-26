# TrustOS Security Threat Model & Agentic Defense Matrix

**Status:** Active Research / Architecture Reference  
**Classification:** Public  
**Version:** 1.0 (October 2026)

## 1. Purpose
This document outlines the threat landscape for autonomous AI agents and maps those threats directly to the TrustOS/SHAPE architecture. The goal of TrustOS is not just to log actions, but to anticipate and neutralize malevolent payloads, backchannel escalations, and supply chain poisoning before execution.

## 2. The 2026 Agentic Threat Landscape

### A. Guidance Injection ("Trojan's Whisper")
Attackers embed adversarial narratives into an agent's bootstrap guidance files (e.g., system prompts, startup scripts). The agent then executes harmful actions (credential exfiltration, persistent backdoors) believing it is following "routine best practices."
*   **Defense:** *Guidance Provenance.* SHAPE requires a cryptographic hash manifest of all bootstrap files. If an agent's behavior changes due to a modified guidance file, the SHAPE gate flags the proposal as "Untrusted Source" and routes to High-Risk human approval.

### B. Runtime Trojan Backdoors
Multi-step attacks manipulate the agent's local state over time to bypass static scanners. The attack lives within the agent's local workspace (harness) rather than a single prompt.
*   **Defense:** *DASGuard Integration.* We treat all agent memory and context files as untrusted. The harness boundary scans control-like text and traces its origin. Only content originating from a verified Trusted Source is allowed to dictate execution flow.

### C. Supply Chain Poisoning
Attackers compromise dependencies (e.g., the `nullifAI` Pickle bypass or LiteLLM PyPI backdoors) to execute code during deserialization or library import, bypassing all prompt-level defenses.
*   **Defense:** *Dependency Forensics.* The Living Ledger records the SHA-256 provenance of every tool, model, and library the agent uses. No dependency enters the execution environment without a verified hash.

## 3. OWASP Agentic Top 10 Mapping

| Threat Vector (OWASP) | SHAPE Defense Mechanism |
| :--- | :--- |
| **ASI01: Agent Goal Hijack** | SHAPE Intent Binding: The human approves a specific, bounded JSON payload, not a generalized instruction. |
| **ASI02: Tool Misuse** | Ephemeral JWT (SALUCA-035): The human authorization token is cryptographically bound to the specific tool and target, preventing lateral movement. |
| **ASI03: Identity & Privilege Abuse** | Target Design: Process-local locks + SQLite atomic claims (`claim_status`) to ensure an agent cannot spoof or replay an approval token. Current State: API paths still rely on process-local RLocks; wiring to atomic SQLite claims is the immediate next priority. |
| **ASI06: Memory/Context Poisoning** | Guidance Provenance (see 2A). The Living Ledger maintains a known-good baseline of context. |
| **ASI07: Insecure Inter-Agent Comm.** | Agents cannot authorize each other. All consequential actions must route through the human-gated SHAPE API. |

## 4. The Multi-Tier Escalation Matrix (Human-in-the-Loop)

A gate is useless if the human isn't aware of it. TrustOS uses a time-bound escalation router based on the risk class of the action.

*   **Tier 1 (Low Risk):** Passive dashboard update. (e.g., Agent reads a public API).
*   **Tier 2 (Medium Risk):** Push notification / Slack / Email with a 1-hour TTL. (e.g., Agent updates a CRM record).
*   **Tier 3 (High Risk):** SMS + Automated Voice Call with a 15-minute TTL. Requires Biometric authentication to approve. (e.g., Agent deploys code).
*   **Tier 4 (Sovereign Risk):** Alert routed to the physical **Sovereign Mesh (Cardputer)**. Requires physical hardware button press to sign the JWT, preventing remote hijacking. (e.g., Financial transfer).

## 5. Global Compliance Integration

### A. India CERT-In (Six-Hour Rule)
The Living Ledger is designed to generate standard incident reports that can be exported within the **six-hour** mandatory reporting window. Logs are structured for **180-day retention**.

### B. India DPDP Act (2023)
TrustOS enforces "Purpose Limitation." When a human approves an action, they are approving the specific data scope. The system defaults to data minimization, and no approval can authorize the exfiltration of PII or children's data without a separate, flagged consent gate.

## 6. Default Fail-Closed Posture
If the network drops, if the human ignores the alert, or if the JWT expires, the action defaults to **DENY**. An agent may not "retry" indefinitely. It must submit a new proposal.
