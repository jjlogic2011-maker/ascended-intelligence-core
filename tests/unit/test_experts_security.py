from experts.security import security_check


def test_expert_field_is_security():
    result = security_check({"type": "security"})
    assert result["expert"] == "security"


def test_echoes_input_task():
    task = {"type": "security", "payload": "scan"}
    result = security_check(task)
    assert result["input"] == task


def test_has_message():
    result = security_check({})
    assert "message" in result and result["message"]


def test_none_task():
    result = security_check(None)
    assert result["expert"] == "security"
    assert result["input"] is None


def test_response_keys():
    result = security_check({"type": "security"})
    assert set(result.keys()) == {"expert", "message", "input"}
