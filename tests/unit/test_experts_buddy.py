from experts.buddy import buddy_respond


def test_expert_field_is_buddy():
    result = buddy_respond({"type": "buddy", "query": "hello"})
    assert result["expert"] == "buddy"


def test_response_includes_query():
    result = buddy_respond({"type": "buddy", "query": "what time is it?"})
    assert result["query"] == "what time is it?"
    assert "what time is it?" in result["message"]


def test_empty_query_returns_greeting():
    result = buddy_respond({"type": "buddy"})
    assert result["query"] == ""
    assert result["message"]


def test_none_task_returns_greeting():
    result = buddy_respond(None)
    assert result["expert"] == "buddy"
    assert result["query"] == ""


def test_response_keys():
    result = buddy_respond({"type": "buddy", "query": "hi"})
    assert set(result.keys()) == {"expert", "message", "query"}
