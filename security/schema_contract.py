"""TRUSTOS-SCHEMA-001: authoritative Draft 2020-12 ingestion boundary.

The JSON Schema files, not duplicated Python tables, define the accepted JSON
record format. Validation is metadata-only and grants no execution authority.
This loader intentionally fails closed if schemas or format validators are absent.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

_SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
_ALLOWED_SCHEMAS = frozenset({
    "authority_request.schema.json", "claim_record.schema.json",
    "event.schema.json", "memory_beacon.schema.json",
})
_FORMATS = FormatChecker()
if "date-time" not in _FORMATS.checkers or "date" not in _FORMATS.checkers:
    raise RuntimeError("Missing RFC3339/date format validators; install jsonschema[format]")


@lru_cache(maxsize=4)
def _get_validator(filename: str) -> Draft202012Validator:
    if filename not in _ALLOWED_SCHEMAS:
        raise ValueError(f"unapproved schema: {filename}")
    path = _SCHEMA_DIR / filename
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=_FORMATS)


def validate_record(filename: str, data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate strictly JSON-compatible metadata, returning an isolated copy.

    No schema defaults are supplied and no model action or authority grant is
    performed. Non-JSON objects and non-finite numbers are rejected. This
    function deliberately uses the same validator as the parity tests.
    """
    if not isinstance(data, Mapping):
        raise ValueError("record must be a JSON object")
    try:
        # JSON objects must have string keys, including nested objects.
        def check(value: Any, seen: set[int]) -> None:
            if isinstance(value, dict) or (isinstance(value, Mapping) and not isinstance(value, dict)):
                if id(value) in seen:
                    raise ValueError("cyclic JSON object")
                seen.add(id(value))
                try:
                    for key, child in value.items():
                        if not isinstance(key, str):
                            raise ValueError("JSON object keys must be strings")
                        check(child, seen)
                finally:
                    seen.remove(id(value))
            elif isinstance(value, list):
                if id(value) in seen:
                    raise ValueError("cyclic JSON array")
                seen.add(id(value))
                try:
                    for child in value:
                        check(child, seen)
                finally:
                    seen.remove(id(value))
            elif not (value is None or isinstance(value, (str, int, float, bool))):
                raise ValueError("record contains a non-JSON value")
        check(data, set())
        candidate = json.loads(json.dumps(dict(data), allow_nan=False))
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValueError(f"record must contain finite JSON values: {exc}") from exc
    try:
        _get_validator(filename).validate(candidate)
    except ValidationError as exc:
        location = ".".join(str(x) for x in exc.absolute_path) or "$"
        raise ValueError(f"{filename}: {location}: {exc.message}") from exc
    return candidate
