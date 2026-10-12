"""Unit tests for CHSH / Bell simulation — working functionality proof."""

from __future__ import annotations

import pytest

from research_lab.quantum.bell_chsh import simulate_chsh


def test_chsh_violates_classical_bound():
    r = simulate_chsh(n_trials=50_000, seed=42)
    assert abs(r.S) > 2.0
    assert r.violates_classical is True


def test_chsh_near_tsirelson():
    r = simulate_chsh(n_trials=100_000, seed=7)
    assert abs(abs(r.S) - r.tsirelson_bound) < 0.15
    assert abs(r.S - r.quantum_prediction) < 0.1


def test_chsh_reproducible_with_seed():
    a = simulate_chsh(n_trials=20_000, seed=123)
    b = simulate_chsh(n_trials=20_000, seed=123)
    assert a.S == b.S
    assert a.experiment_id == b.experiment_id


def test_chsh_resource_limits():
    with pytest.raises(ValueError):
        simulate_chsh(n_trials=100)
    with pytest.raises(ValueError):
        simulate_chsh(n_trials=6_000_000)


def test_chsh_has_integrity_fields():
    r = simulate_chsh(n_trials=10_000, seed=1)
    d = r.to_dict()
    assert "classification" in d
    assert "limitations" in d
    assert "consciousness" in d["limitations"].lower() or "spiritual" in d["limitations"].lower()
