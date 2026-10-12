"""
Validation Agent — classifies theoretical claims and records verification status.

Never elevates a claim beyond the evidence. Every claim receives one of:
ESTABLISHED | SUPPORTED | PRELIMINARY | HYPOTHESIS | SPECULATIVE | OPERATIONAL
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from research_lab.agents.evidence.ledger import append_evidence


ALLOWED = {
    "ESTABLISHED",
    "SUPPORTED",
    "PRELIMINARY",
    "HYPOTHESIS",
    "SPECULATIVE",
    "OPERATIONAL",
}


@dataclass
class ValidatedClaim:
    claim_id: str
    statement: str
    classification: str
    evidence_summary: str
    working_functionality: bool
    limitations: str
    references: List[str]


def validate_claim(
    statement: str,
    classification: str,
    evidence_summary: str,
    *,
    working_functionality: bool = False,
    limitations: str = "",
    references: Optional[List[str]] = None,
    agent_name: str = "ValidationAgent",
) -> ValidatedClaim:
    if classification not in ALLOWED:
        raise ValueError(f"Invalid classification: {classification}")

    lowered = statement.lower()
    forbidden = [
        "quantum mechanics proves consciousness",
        "quantum proves consciousness",
        "consciousness is quantum",
        "quantum healing is established",
        "432 hz heals",
    ]
    for phrase in forbidden:
        if phrase in lowered and classification in {"ESTABLISHED", "SUPPORTED"}:
            classification = "SPECULATIVE"
            limitations = (
                (limitations + " ") if limitations else ""
            ) + "Auto-downgraded: unsupported consciousness/healing claim."

    claim_id = str(abs(hash(statement)) % (10**10))
    claim = ValidatedClaim(
        claim_id=claim_id,
        statement=statement,
        classification=classification,
        evidence_summary=evidence_summary,
        working_functionality=working_functionality,
        limitations=limitations or "None stated",
        references=references or [],
    )

    append_evidence(
        agent=agent_name,
        action="validate_claim",
        claim=statement,
        classification=classification,
        evidence_type="validation",
        payload={
            "claim_id": claim.claim_id,
            "working_functionality": working_functionality,
            "evidence_summary": evidence_summary,
            "limitations": claim.limitations,
            "references": claim.references,
        },
        status="verified" if working_functionality else "recorded",
    )
    return claim
