"""Unit tests for classical CHSH simulation."""

import pytest

from research.quantum import run_chsh_simulation


def test_chsh_classical_bound():
    result = run_chsh_simulation(n_trials=5000, seed=123)
    assert result.n_trials == 5000
    assert abs(result.S) <= result.classical_bound + 1e-6
    assert result.violates_classical is False
    assert result.evidence_class == "PRELIMINARY"
    assert "consciousness" not in result.notes.lower()
    assert result.method.startswith("classical")


def test_chsh_reproducible():
    a = run_chsh_simulation(n_trials=2000, seed=7)
    b = run_chsh_simulation(n_trials=2000, seed=7)
    assert a.S == b.S
    assert a.experiment_id == b.experiment_id


def test_chsh_invalid_trials():
    with pytest.raises(ValueError):
        run_chsh_simulation(n_trials=10)
