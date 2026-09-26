"""AIRI-DNA — deterministic canonical fingerprint for artifacts.

Produces a SHA-256 fingerprint over a canonical JSON encoding of
declared artifact attributes.

IMPORTANT: This does NOT prove identity, authenticity, authorship, or
correctness. It only allows two parties who agree on the canonical
encoding to detect whether the declared attributes are identical.

Canonicalization:
- keys sorted lexicographically
- UTF-8 encoding
- JSON separators (",", ":") with no surrounding whitespace
- ensure_ascii=False
- NaN / Infinity disallowed
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

_CANONICAL_SEPARATORS = (",", ":")


@dataclass(frozen=True)
class ContributionLineage:
    parent_artifact_id: str | None
    contribution_type: str
    contributor: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AIRIDNA:
    artifact_id: str
    creator: str
    version: str
    timestamp: str
    provenance: dict
    lineage: list
    policy_state: str
    content_hash: str

    def to_canonical_dict(self) -> dict:
        return {
            "artifact_id": self.artifact_id,
            "content_hash": self.content_hash,
            "creator": self.creator,
            "lineage": [l.to_dict() for l in self.lineage],
            "policy_state": self.policy_state,
            "provenance": self.provenance,
            "timestamp": self.timestamp,
            "version": self.version,
        }

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=_CANONICAL_SEPARATORS,
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")

    def fingerprint(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def fingerprint_content(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def build_dna(
    *,
    artifact_id: str,
    creator: str,
    version: str,
    timestamp: str,
    provenance: dict | None,
    lineage: list | None = None,
    policy_state: str = "UNSPECIFIED",
    content: bytes | None = None,
    content_hash: str | None = None,
) -> AIRIDNA:
    if provenance is None:
        raise ValueError("provenance is required")
    if not isinstance(provenance, dict):
        raise ValueError("provenance must be a mapping")
    if content_hash is None:
        if content is None:
            raise ValueError("must supply content or content_hash")
        content_hash = fingerprint_content(content)
    return AIRIDNA(
        artifact_id=artifact_id,
        creator=creator,
        version=version,
        timestamp=timestamp,
        provenance=provenance,
        lineage=list(lineage or []),
        policy_state=policy_state,
        content_hash=content_hash,
    )
