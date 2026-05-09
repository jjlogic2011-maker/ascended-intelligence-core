import importlib
import api.infrastructure.config as config_mod
from api.infrastructure.config import _parse_max_agents


# --- _parse_max_agents helper ---

def test_parse_valid_integer():
    assert _parse_max_agents("5") == 5


def test_parse_zero():
    assert _parse_max_agents("0") == 0


def test_parse_invalid_string_returns_default():
    assert _parse_max_agents("abc") == 10


def test_parse_none_returns_default():
    assert _parse_max_agents(None) == 10


def test_parse_float_string_returns_default():
    assert _parse_max_agents("3.5") == 10


def test_custom_default():
    assert _parse_max_agents("bad", default=99) == 99


# --- CONFIG env var integration ---

def test_defaults(monkeypatch):
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("AICI_MAX_AGENTS", raising=False)
    importlib.reload(config_mod)
    assert config_mod.CONFIG["env"] == "production"
    assert config_mod.CONFIG["max_agents"] == 10


def test_custom_env(monkeypatch):
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("AICI_MAX_AGENTS", "25")
    importlib.reload(config_mod)
    assert config_mod.CONFIG["env"] == "development"
    assert config_mod.CONFIG["max_agents"] == 25


def test_invalid_max_agents_falls_back(monkeypatch):
    monkeypatch.setenv("AICI_MAX_AGENTS", "not-a-number")
    importlib.reload(config_mod)
    assert config_mod.CONFIG["max_agents"] == 10
