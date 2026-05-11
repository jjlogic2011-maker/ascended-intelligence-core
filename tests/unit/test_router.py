from agents.router import route_task


def test_security_type_routes_to_security_check():
    result = route_task({"type": "security"})
    assert result["expert"] == "security"


def test_report_type_routes_to_generate_report():
    result = route_task({"type": "report"})
    assert result["status"] == "success"


def test_missing_type_defaults_to_report():
    result = route_task({"data": "no type key"})
    assert result["status"] == "success"


def test_buddy_type_routes_to_buddy_respond():
    result = route_task({"type": "buddy", "query": "hello"})
    assert result["expert"] == "buddy"


def test_unknown_type_falls_through_to_report():
    result = route_task({"type": "unknown_expert"})
    assert result["status"] == "success"


def test_security_task_echoes_input():
    task = {"type": "security", "payload": "test"}
    result = route_task(task)
    assert result["input"] == task
