"""Strict validation for Memory Beacons (closed-world contract)."""
from __future__ import annotations

import re
from typing import Any, Mapping, NotRequired, TypedDict, cast


class MemoryBeacon(TypedDict):
    beacon_id: str
    date: str
    mission: str
    outcome: str
    confidence: str
    participants: NotRequired[list[str]]
    emotional_tone: NotRequired[str]
    difficulty_burden: NotRequired[str]
    lesson_learned: NotRequired[str]
    future_recall_cues: NotRequired[list[str]]
    cross_ledger_link: NotRequired[str]


_REQUIRED = frozenset({"beacon_id", "date", "mission", "outcome", "confidence"})
_ALLOWED = _REQUIRED | frozenset(
    {
        "participants",
        "emotional_tone",
        "difficulty_burden",
        "lesson_learned",
        "future_recall_cues",
        "cross_ledger_link",
    }
)

_STRING_FIELDS = frozenset(
    {
        "beacon_id",
        "date",
        "mission",
        "outcome",
        "emotional_tone",
        "difficulty_burden",
        "lesson_learned",
        "cross_ledger_link",
    }
)

_STRING_ARRAY_FIELDS = frozenset({"participants", "future_recall_cues"})

_CONFIDENCE_ENUM = frozenset(
    {"ledgered", "reconstructed", "claimed", "unverified", "disputed"}
)

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

    for field in _STRING_ARRAY_FIELDS & keys:
        value = data[field]
        if not isinstance(value, list):
            raise ValueError(f"{field} must be an array")
        if any(not isinstance(item, str) for item in value):
            raise ValueError(f"{field} items must be strings")

    return cast(MemoryBeacon, dict(data))
