from experts.report import generate_report


def test_returns_success_status():
    result = generate_report({"key": "value"})
    assert result["status"] == "success"


def test_echoes_data():
    data = {"key": "value", "nested": [1, 2]}
    result = generate_report(data)
    assert result["data"] == data


def test_none_data_by_default():
    result = generate_report()
    assert result["data"] is None


def test_explicit_none_data():
    result = generate_report(None)
    assert result["data"] is None


def test_has_message():
    result = generate_report("anything")
    assert "message" in result and result["message"]


def test_string_data():
    result = generate_report("plain string")
    assert result["data"] == "plain string"
