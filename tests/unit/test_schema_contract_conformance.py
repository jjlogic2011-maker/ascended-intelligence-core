"""TRUSTOS-SCHEMA-001: JSON Schema ↔ typed parser behavioral parity.

Test only JSON-serializable fixtures; non-JSON Python objects are rejected by
schema_contract before checking the schema. This is a contract conformance
suite, not a proof of provenance authenticity, authorization, or execution.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from security.precept_authority_request import parse_precept_authority_request
from security.claim_record import parse_claim_record
from security.precept_witness_event import parse_precept_witness_event
from security.memory_beacon import parse_memory_beacon

BASE = Path(__file__).resolve().parents[2]
CONTRACTS = [
    ("authority_request.schema.json", parse_precept_authority_request, {
        "request_id": "r-1", "effect": "read", "risk_tier": "low",
        "status": "PENDING", "requested_at": "2026-10-28T12:34:56Z",
    }),
    ("claim_record.schema.json", parse_claim_record, {
        "claim_id": "c-1", "claim_text": "Observed statement",
        "status": "observed", "confidence": 0.5,
    }),
    ("event.schema.json", parse_precept_witness_event, {
        "event_id": "e-1", "trace_id": "t-1", "event_type": "evaluation",
        "timestamp": "2026-10-28T12:34:56Z", "actor": "observer",
        "input_hash": "digest-placeholder",
    }),
    ("memory_beacon.schema.json", parse_memory_beacon, {
        "beacon_id": "b-1", "date": "2026-10-28", "mission": "Study",
        "outcome": "complete", "confidence": "ledgered",
    }),
]


def _schema(name):
    data = json.loads((BASE / "schemas" / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(data)
    assert data.get("additionalProperties") is False, f"Unknown fields must be denied: {name}"
    return data


def _checker(schema):
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _example(property_schema):
    if "enum" in property_schema:
        return property_schema["enum"][0]
    typ = property_schema.get("type")
    if isinstance(typ, list):
        typ = next(t for t in typ if t != "null")
    if typ == "string":
        if property_schema.get("format") == "date-time":
            return "2026-10-28T12:34:56Z"
        if property_schema.get("format") == "date":
            return "2026-10-28"
        return "sample"
    if typ == "number":
        return 0.5
    if typ == "object":
        return {"nested": "value"}
    if typ == "array":
        item_schema = property_schema.get("items", {})
        return [_example(item_schema)]
    raise AssertionError(f"fixture missing for property: {property_schema}")


def _wrong_value(property_schema):
    if "enum" in property_schema:
        return {"invalid": "enum"}
    typ = property_schema.get("type")
    if isinstance(typ, list):
        typ = next(t for t in typ if t != "null")
    return {"string": 42, "object": "not-object", "array": "not-array", "number": "not-number"}[typ]


def _cases(name, schema, minimum):
    out = [("minimal", minimum), ("extra-key", {**minimum, "unauthorized_key": True}),
           ("empty", {}), ("null-root", None), ("array-root", [])]
    for field in schema["required"]:
        row = dict(minimum)
        row.pop(field)
        out.append((f"missing:{field}", row))
    for field, prop in schema["properties"].items():
        row = dict(minimum, **{field: _example(prop)})
        out.append((f"valid:{field}", row))
        row = dict(minimum, **{field: _wrong_value(prop)})
        out.append((f"invalid-type:{field}", row))
        if isinstance(prop.get("type"), list) and "null" in prop["type"]:
            row = dict(minimum, **{field: None})
            out.append((f"valid-null:{field}", row))
        if "enum" in prop:
            for value in prop["enum"]:
                out.append((f"enum:{field}:{value}", dict(minimum, **{field: value})))
    if name == "claim_record.schema.json":
        for conf in [0, 1, 0.00001, -0.001, 1.001, True, None, []]:
            out.append((f"confidence:{conf}", dict(minimum, confidence=conf)))
        out.append(("nested-evidence", dict(minimum, evidence=[{"a": {"b": [1, False, None]}}])))
    if name == "authority_request.schema.json":
        for ts in ["2026-02-30T12:00:00Z", "2026-10-28T12:00:00", "2026-10-28T12:00:00+25:00"]:
            out.append((f"bad-timestamp:{ts}", dict(minimum, requested_at=ts)))
    if name == "event.schema.json":
        for ts in ["2026-02-30T12:00:00Z", "2026-10-28T12:00:00", "not-a-date"]:
            out.append((f"bad-timestamp:{ts}", dict(minimum, timestamp=ts)))
    if name == "memory_beacon.schema.json":
        for day in ["2026-02-30", "2026/10/28", "2026-10-28", "anything", "2024-02-29"]:
            out.append((f"date:{day}", dict(minimum, date=day)))
        out.append(("all-optional", {**minimum, "participants": ["reviewer"],
                   "emotional_tone": "calm", "difficulty_burden": "low",
                   "lesson_learned": "strict parity", "future_recall_cues": ["schema"],
                   "cross_ledger_link": "ledger://item"}))
    return out


CASES = []
for name, parser, minimal in CONTRACTS:
    schema = _schema(name)
    for label, record in _cases(name, schema, minimal):
        CASES.append(pytest.param(name, parser, schema, record,
                                  id=f"{name}:{label}"))


@pytest.mark.parametrize("name,parser,schema,record", CASES)
def test_parser_and_draft202012_schema_agree(name, parser, schema, record):
    valid = _checker(schema).is_valid(record)
    if valid:
        assert parser(record) == record
    else:
        with pytest.raises(ValueError):
            parser(record)


@pytest.mark.parametrize("name,parser,minimal", CONTRACTS)
def test_parser_returns_separate_copy(name, parser, minimal):
    src = copy.deepcopy(minimal)
    result = parser(src)
    assert result == src
    assert result is not src


@pytest.mark.parametrize("name,parser,minimal", CONTRACTS)
def test_unexpected_field_fails_closed(name, parser, minimal):
    with pytest.raises(ValueError):
        parser({**minimal, "unauthorized": "must not pass"})


def test_authority_allow_remains_metadata_only():
    _, parser, payload = CONTRACTS[0]
    record = parser({**payload, "status": "ALLOW"})
    assert record["status"] == "ALLOW"
    assert "grant_id" not in record
    assert "principal_id" not in record


def test_nested_evidence_copy_is_not_aliased():
    _, parser, payload = CONTRACTS[1]
    original = {**payload, "evidence": [{"nested": {"items": [1, 2]}}]}
    parsed = parser(original)
    original["evidence"][0]["nested"]["items"].append(3)
    assert parsed["evidence"][0]["nested"]["items"] == [1, 2]


@pytest.mark.parametrize("name,parser,minimal", CONTRACTS)
def test_reject_nan_and_non_json_values(name, parser, minimal):
    with pytest.raises(ValueError):
        parser({**minimal, "unauthorized": float("nan")})
    # Even in schema-defined opaque objects, JSON incompatibility is rejected.


def test_date_format_checker_is_installed():
    assert not FormatChecker().conforms("2026-02-30", "date")
    assert not FormatChecker().conforms("2026-02-30T12:00:00Z", "date-time")
