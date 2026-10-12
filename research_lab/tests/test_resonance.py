"""Unit tests for Resonance Laboratory."""

from __future__ import annotations

import numpy as np
import pytest

from research_lab.resonance.signal_lab import (
    compare_432_vs_440,
    generate_tone,
    run_resonance_experiment,
)


def test_generate_tone_shape():
    t, sig = generate_tone(440.0, duration_sec=0.1, sample_rate=8000)
    assert len(t) == len(sig) == 800
    assert abs(np.max(np.abs(sig)) - 0.5) < 0.05


def test_compare_432_440_peaks_near_targets():
    comp = compare_432_vs_440(duration_sec=0.5, sample_rate=22050, seed=1)
    for target in ("432.0", "440.0"):
        peaks = comp["comparison"][target]["peak_frequencies_hz"]
        assert any(abs(p - float(target)) < 15.0 for p in peaks[:3])


def test_resonance_experiment_id_stable():
    a = run_resonance_experiment([432.0], duration_sec=0.2, seed=5)
    b = run_resonance_experiment([432.0], duration_sec=0.2, seed=5)
    assert a.experiment_id == b.experiment_id


def test_no_physiological_claim_in_result():
    r = run_resonance_experiment([440.0], duration_sec=0.1, seed=0)
    text = (r.classification + " " + r.limitations).lower()
    assert "speculative" in text or "not claimed" in text
