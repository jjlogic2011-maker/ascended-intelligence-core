"""Strict validation for PRECEPT Witness Events."""
from __future__ import annotations
import re
from typing import Any, Mapping, NotRequired, TypedDict, cast

class PreceptWitnessEvent(TypedDict):
    event_id: str
    trace_id: str
    event_type: str
    timestamp: str
    actor: str
    input_hash: str
    parent_event_id: NotRequired[str | None]
    tool: NotRequired[str | None]
    connector: NotRequired[str | None]
    authority_request_id: NotRequired[str | None]
    output_hash: NotRequired[str | None]
    claim_ids: NotRequired[list[str]]
    attributes: NotRequired[dict[str, Any]]

_REQUIRED = frozenset({"event_id", "trace_id", "event_type", "timestamp", "actor", "input_hash"})
_ALLOWED = _REQUIRED | frozenset({"parent_event_id", "tool", "connector", "authority_request_id", "output_hash", "claim_ids", "attributes"})
_STRING_FIELDS = frozenset({"event_id", "trace_id", "event_type", "actor", "input_hash"})
_NULLABLE_STRING_FIELDS = frozenset({"parent_event_id", "tool", "connector", "authority_request_id", "output_hash"})
_RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$")

def _check_datetime(value: object, name: str) -> None:
    if not isinstance(value, str) or not _RFC3339.fullmatch(value):
        raise ValueError(f"{name} must be an RFC 3339 date-time string")

def parse_precept_witness_event(data: Mapping[str, Any]) -> PreceptWitnessEvent:
    if not isinstance(data, Mapping):
        raise ValueError("Witness event must be a JSON object")
    
    keys = set(data)
    if any(not isinstance(key, str) for key in keys):
        raise ValueError("Witness event keys must be strings")
    if keys - _ALLOWED:
        raise ValueError(f"unknown witness event fields: {sorted(keys - _ALLOWED)}")
    if _REQUIRED - keys:
        raise ValueError(f"missing required fields: {sorted(_REQUIRED - keys)}")
        
    for field in _STRING_FIELDS & keys:
        if not isinstance(data[field], str):
            raise ValueError(f"{field} must be a string")
            
    for field in _NULLABLE_STRING_FIELDS & keys:
        if data[field] is not None and not isinstance(data[field], str):
            raise ValueError(f"{field} must be a string or null")
            
    if "claim_ids" in keys:
        if not isinstance(data["claim_ids"], list) or any(not isinstance(item, str) for item in data["claim_ids"]):
            raise ValueError("claim_ids must be an array of strings")
            
    if "attributes" in keys:
        if not isinstance(data["attributes"], dict):
            raise ValueError("attributes must be an object")
            
    _check_datetime(data["timestamp"], "timestamp")
    
    return cast(PreceptWitnessEvent, dict(data))
