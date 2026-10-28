import pytest
from security.precept_authority_request import parse_precept_authority_request

def minimal(**overrides):
    data = {"request_id": "req-1", "effect": "read", "risk_tier": "low", "status": "PENDING", "requested_at": "2026-10-27T16:14:00-07:00"}
    data.update(overrides)
    return data

def test_minimal_schema_record():
    assert parse_precept_authority_request(minimal()) == minimal()

def test_all_documented_fields_and_nullables():
    record = minimal(target="example", scope={"unconstrained_nested_object": [1, 2]}, requested_by="operator", approved_by=None, rollback_plan=None, decided_at="2026-10-27T23:20:00Z", status="ALLOW", risk_tier="critical")
    assert parse_precept_authority_request(record) == record

@pytest.mark.parametrize("field", ["request_id", "effect", "risk_tier", "status", "requested_at"])
def test_missing_required_field_rejected(field):
    data = minimal(); del data[field]
    with pytest.raises(ValueError, match="missing required"): parse_precept_authority_request(data)

@pytest.mark.parametrize("field", ["delegation_chain", "cost_budget", "resource_scope"])
def test_unsourced_fields_rejected(field):
    with pytest.raises(ValueError, match="unknown authority request fields"): parse_precept_authority_request(minimal(**{field: "not in schema"}))

@pytest.mark.parametrize("bad", ["APPROVED", "EXECUTED", "UNKNOWN"])
def test_shape_statuses_are_not_precept_statuses(bad):
    with pytest.raises(ValueError, match="status is outside"): parse_precept_authority_request(minimal(status=bad))

def test_unknown_risk_tier_rejected():
    with pytest.raises(ValueError, match="risk_tier is outside"): parse_precept_authority_request(minimal(risk_tier="extreme"))

@pytest.mark.parametrize("field,value", [("request_id", 9), ("effect", None), ("target", None), ("scope", ["not an object"]), ("requested_by", 0), ("approved_by", []), ("rollback_plan", 7), ("decided_at", False)])
def test_declared_types_enforced(field, value):
    with pytest.raises(ValueError): parse_precept_authority_request(minimal(**{field: value}))

@pytest.mark.parametrize("bad", ["tomorrow", "2026-10-27", "2026-10-27T16:14:00", "2026-13-27T16:14:00Z"])
def test_bad_requested_at_rejected(bad):
    with pytest.raises(ValueError, match="date-time"): parse_precept_authority_request(minimal(requested_at=bad))

def test_bad_decided_at_rejected():
    with pytest.raises(ValueError, match="date-time"): parse_precept_authority_request(minimal(decided_at="later"))

def test_parser_returns_copy_not_mutable_grant():
    original = minimal(status="ALLOW")
    result = parse_precept_authority_request(original)
    assert result == original and result is not original
    assert "grant_id" not in result and "principal_id" not in result

def test_unhashable_invalid_enum_types_are_rejected():
    with pytest.raises(ValueError, match="risk_tier is outside"): parse_precept_authority_request(minimal(risk_tier=[]))
    with pytest.raises(ValueError, match="status is outside"): parse_precept_authority_request(minimal(status={}))

def test_non_string_property_names_rejected():
    with pytest.raises(ValueError, match="keys must be strings"): parse_precept_authority_request({**minimal(), 1: "invalid"})
