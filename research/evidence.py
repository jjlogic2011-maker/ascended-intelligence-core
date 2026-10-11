"""Scientific Evidence Registry — claims, sources, classifications.

In-memory store for the initial release. Can later be backed by SQLite/Postgres.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


VALID_CLASSES = {
    "ESTABLISHED",
    "SUPPORTED",
    "PRELIMINARY",
    "HYPOTHESIS",
    "SPECULATIVE",
}


@dataclass
class Claim:
    claim_id: str
    statement: str
    evidence_class: str
    domain: str  # quantum | resonance | neuroscience | other
    sources: List[Dict[str, str]] = field(default_factory=list)
    notes: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EvidenceRegistry:
    def __init__(self) -> None:
        self._claims: Dict[str, Claim] = {}
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        """Seed a few carefully labeled claims so the registry is never empty."""
        seeds = [
            {
                "statement": "CHSH inequality can be violated by quantum systems up to Tsirelson's bound 2√2.",
                "evidence_class": "ESTABLISHED",
                "domain": "quantum",
                "sources": [
                    {"title": "Bell (1964) / CHSH (1969) foundational results",
                     "note": "Textbook quantum information result"}
                ],
                "notes": "Mathematical and experimental result in quantum physics. Does not imply consciousness.",
            },
            {
                "statement": "Pure sinusoidal tones at 432 Hz and 440 Hz can be generated and spectrally analysed numerically.",
                "evidence_class": "ESTABLISHED",
                "domain": "resonance",
                "sources": [],
                "notes": "Trivial numerical fact. No biological claim.",
            },
            {
                "statement": "Exposure to 432 Hz or 440 Hz audio produces measurable health or consciousness effects in humans.",
                "evidence_class": "SPECULATIVE",
                "domain": "resonance",
                "sources": [],
                "notes": "No strong reproducible evidence supports general health or consciousness claims.",
            },
            {
                "statement": "Quantum mechanics provides a physical mechanism that explains or measures consciousness.",
                "evidence_class": "SPECULATIVE",
                "domain": "quantum",
                "sources": [],
                "notes": "Explicitly outside the scope of this laboratory. Forbidden as an asserted claim.",
            },
        ]
        for s in seeds:
            self.add_claim(**s)

    def add_claim(
        self,
        statement: str,
        evidence_class: str,
        domain: str,
        sources: Optional[List[Dict[str, str]]] = None,
        notes: str = "",
        claim_id: Optional[str] = None,
    ) -> Claim:
        if evidence_class not in VALID_CLASSES:
            raise ValueError(f"evidence_class must be one of {VALID_CLASSES}")
        cid = claim_id or str(uuid.uuid4())
        claim = Claim(
            claim_id=cid,
            statement=statement,
            evidence_class=evidence_class,
            domain=domain,
            sources=sources or [],
            notes=notes,
        )
        self._claims[cid] = claim
        return claim

    def list_claims(
        self,
        domain: Optional[str] = None,
        evidence_class: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        out = []
        for c in self._claims.values():
            if domain and c.domain != domain:
                continue
            if evidence_class and c.evidence_class != evidence_class:
                continue
            out.append(c.to_dict())
        return sorted(out, key=lambda x: x["created_at"])

    def get(self, claim_id: str) -> Optional[Dict[str, Any]]:
        c = self._claims.get(claim_id)
        return c.to_dict() if c else None
