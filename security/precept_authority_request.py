"""Strict, non-executing PRECEPT AuthorityRequest ingestion.

A request status of ALLOW does not represent a SHAPE authorization or grant.
"""
from __future__ import annotations
import re
from typing import Any, Mapping, NotRequired, TypedDict, cast
from security.schema_contract import validate_record

class PreceptAuthorityRequest(TypedDict):
    request_id: str
    effect: str
    risk_tier: str
    status: str
    requested_at: str
    target: NotRequired[str]
    scope: NotRequired[dict[str, Any]]
    requested_by: NotRequired[str]
    approved_by: NotRequired[str | None]
    rollback_plan: NotRequired[str | None]
    decided_at: NotRequired[str | None]

_REQUIRED = frozenset({"request_id", "effect", "risk_tier", "status", "requested_at"})
_ALLOWED = _REQUIRED | frozenset({"target", "scope", "requested_by", "approved_by", "rollback_plan", "decided_at"})
_STRING_FIELDS = frozenset({"request_id", "effect", "target", "requested_by"})
_NULLABLE_STRING_FIELDS = frozenset({"approved_by", "rollback_plan", "decided_at"})
_RISK_TIERS = frozenset({"low", "medium", "high", "critical"})
_REQUEST_STATUSES = frozenset({"PENDING", "ALLOW", "DENY", "MODIFY", "DEFER", "ESCALATE"})
_RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$")

def _check_datetime(value: object, name: str) -> None:
    if not isinstance(value, str) or not _RFC3339.fullmatch(value):
        raise ValueError(f"{name} must be an RFC 3339 date-time string")
    # Calendar validity and timezone semantics are checked by the schema oracle.

def parse_precept_authority_request(data: Mapping[str, Any]) -> PreceptAuthorityRequest:
    if not isinstance(data, Mapping):
        raise ValueError("PRECEPT authority request must be a JSON object")
    keys = set(data)
    if any(not isinstance(key, str) for key in keys):
        raise ValueError("authority request keys must be strings")
    if keys - _ALLOWED:
        raise ValueError(f"unknown authority request fields: {sorted(keys - _ALLOWED)}")
    if _REQUIRED - keys:
        raise ValueError(f"missing required fields: {sorted(_REQUIRED - keys)}")
    for field in _STRING_FIELDS & keys:
        if not isinstance(data[field], str):
            raise ValueError(f"{field} must be a string")
    for field in _NULLABLE_STRING_FIELDS & keys:
        if data[field] is not None and not isinstance(data[field], str):
            raise ValueError(f"{field} must be a string or null")
    if "scope" in keys and not isinstance(data["scope"], dict):
        raise ValueError("scope must be an object")
    if not isinstance(data["risk_tier"], str) or data["risk_tier"] not in _RISK_TIERS:
        raise ValueError("risk_tier is outside the schema enum")
    if not isinstance(data["status"], str) or data["status"] not in _REQUEST_STATUSES:
        raise ValueError("status is outside the schema enum")
    _check_datetime(data["requested_at"], "requested_at")
    if "decided_at" in keys and data["decided_at"] is not None:
        _check_datetime(data["decided_at"], "decided_at")
    return cast(PreceptAuthorityRequest, validate_record("authority_request.schema.json", data))
