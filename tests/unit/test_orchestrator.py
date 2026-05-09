import pytest
from core.orchestrator import Orchestrator


@pytest.fixture
def orch():
    return Orchestrator()


def test_none_task_returns_error(orch):
    result = orch.run(None)
    assert "error" in result


def test_empty_dict_returns_error(orch):
    result = orch.run({})
    assert "error" in result


def test_valid_report_task(orch):
    result = orch.run({"type": "report"})
    assert result["status"] == "executed"
    assert "result" in result


def test_valid_security_task(orch):
    result = orch.run({"type": "security"})
    assert result["status"] == "executed"
    assert result["result"]["expert"] == "security"


def test_default_task_type(orch):
    result = orch.run({"payload": "no type"})
    assert result["status"] == "executed"
    assert result["result"]["status"] == "success"


def test_response_shape_is_consistent(orch):
    for task in [{"type": "report"}, {"type": "security"}]:
        result = orch.run(task)
        assert "status" in result
        assert "result" in result
