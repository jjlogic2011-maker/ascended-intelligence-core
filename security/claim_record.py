"""Strict validation for ClaimRecord."""
from __future__ import annotations
from typing import Any, Mapping, NotRequired, TypedDict, cast

class ClaimRecord(TypedDict):
    claim_id: str
    claim_text: str
    status: str
    confidence: float
    source: NotRequired[str]
    evidence: NotRequired[list[dict[str, Any]]]
    review_date: NotRequired[str]
    public_safe_wording: NotRequired[str]

_REQUIRED = frozenset({"claim_id", "claim_text", "status", "confidence"})
_ALLOWED = _REQUIRED | frozenset({"source", "evidence", "review_date", "public_safe_wording"})
_STATUS_ENUM = frozenset({"observed", "claimed", "verified", "proven", "disputed", "speculative", "interpretation", "spiritual_evaluation", "revoked"})
_STRING_FIELDS = frozenset({"claim_id", "claim_text", "source", "review_date", "public_safe_wording"})

def parse_claim_record(data: Mapping[str, Any]) -> ClaimRecord:
    if not isinstance(data, Mapping):
        raise ValueError("ClaimRecord must be a JSON object")
    keys = set(data)
    if any(not isinstance(key, str) for key in keys):
        raise ValueError("ClaimRecord keys must be strings")
    if keys - _ALLOWED:
        raise ValueError(f"unknown ClaimRecord fields: {sorted(keys - _ALLOWED)}")
    if _REQUIRED - keys:
        raise ValueError(f"missing required fields: {sorted(_REQUIRED - keys)}")
    for field in _STRING_FIELDS & keys:
        if not isinstance(data[field], str):
            raise ValueError(f"{field} must be a string")
    if data["status"] not in _STATUS_ENUM:
        raise ValueError(f"status must be one of {sorted(_STATUS_ENUM)}")
    conf = data["confidence"]
    if isinstance(conf, bool) or not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
        raise ValueError("confidence must be a number between 0.0 and 1.0")
    if "evidence" in keys and (not isinstance(data["evidence"], list) or any(not isinstance(item, dict) for item in data["evidence"])):
        raise ValueError("evidence must be an array of objects")
    return cast(ClaimRecord, dict(data))
