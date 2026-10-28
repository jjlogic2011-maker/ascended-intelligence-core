"""Strict validation for Memory Beacons."""
from __future__ import annotations
import re
from typing import Any, Mapping, NotRequired, TypedDict, cast

class MemoryBeacon(TypedDict):
    beacon_id: str
    date: str
    mission: str
    outcome: str
    confidence: str
    # Optional fields that may exist based on the full schema
    future_recall_cues: NotRequired[list[str]]
    cross_ledger_link: NotRequired[str]

_REQUIRED = frozenset({
    "beacon_id", "date", "mission", "outcome", "confidence"
})
_ALLOWED = _REQUIRED | frozenset({"future_recall_cues", "cross_ledger_link"})

_STRING_FIELDS = frozenset({
    "beacon_id", "date", "mission", "outcome", "cross_ledger_link"
})

_CONFIDENCE_ENUM = frozenset({
    "ledgered", 
    "reconstructed", 
    "claimed", 
    "unverified", 
    "disputed"
})

_DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def _check_date(value: object, name: str) -> None:
    if not isinstance(value, str) or not _DATE_REGEX.fullmatch(value):
        raise ValueError(f"{name} must be a YYYY-MM-DD date string")

def parse_memory_beacon(data: Mapping[str, Any]) -> MemoryBeacon:
    if not isinstance(data, Mapping):
        raise ValueError("MemoryBeacon must be a JSON object")
    
    keys = set(data)
    if any(not isinstance(key, str) for key in keys):
        raise ValueError("MemoryBeacon keys must be strings")
    if keys - _ALLOWED:
        raise ValueError(f"unknown MemoryBeacon fields: {sorted(keys - _ALLOWED)}")
    if _REQUIRED - keys:
        raise ValueError(f"missing required fields: {sorted(_REQUIRED - keys)}")
        
    for field in _STRING_FIELDS & keys:
        if not isinstance(data[field], str):
            raise ValueError(f"{field} must be a string")
            
    _check_date(data["date"], "date")
    
    if data["confidence"] not in _CONFIDENCE_ENUM:
        raise ValueError(f"confidence must be one of {sorted(_CONFIDENCE_ENUM)}")
        
    if "future_recall_cues" in keys:
        if not isinstance(data["future_recall_cues"], list):
            raise ValueError("future_recall_cues must be an array")
        if any(not isinstance(item, str) for item in data["future_recall_cues"]):
            raise ValueError("future_recall_cues items must be strings")
            
    return cast(MemoryBeacon, dict(data))
