from unittest.mock import MagicMock
import security.auth as auth_module


def _make_request(key_value):
    req = MagicMock()
    req.headers.get.return_value = key_value
    return req


def test_verify_valid_key(monkeypatch):
    monkeypatch.setattr(auth_module, "API_KEY", "secret-key")
    assert auth_module.verify(_make_request("secret-key")) is True


def test_verify_invalid_key(monkeypatch):
    monkeypatch.setattr(auth_module, "API_KEY", "secret-key")
    assert auth_module.verify(_make_request("wrong-key")) is False


def test_verify_missing_header(monkeypatch):
    monkeypatch.setattr(auth_module, "API_KEY", "secret-key")
    assert auth_module.verify(_make_request(None)) is False


def test_verify_empty_string(monkeypatch):
    monkeypatch.setattr(auth_module, "API_KEY", "secret-key")
    assert auth_module.verify(_make_request("")) is False


def test_verify_default_insecure_key():
    # Confirms default key is the insecure placeholder — should never match real requests.
    import importlib, os
    saved = os.environ.pop("AICI_API_KEY", None)
    try:
        importlib.reload(auth_module)
        assert auth_module.API_KEY == "change-me"
    finally:
        if saved is not None:
            os.environ["AICI_API_KEY"] = saved
        importlib.reload(auth_module)
