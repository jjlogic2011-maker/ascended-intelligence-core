"""Unit tests for resonance waveform module."""

import pytest

from research.resonance import generate_and_analyze


def test_resonance_basic():
    result = generate_and_analyze(
        frequencies_hz=[440.0], sample_rate=8000, duration_s=0.5
    )
    assert result.sample_rate == 8000
    assert 440.0 in result.frequencies_hz or any(
        abs(f - 440.0) < 5 for f in result.peak_frequencies
    )
    assert result.evidence_class == "ESTABLISHED"
    assert "healing" not in result.notes.lower()
    assert "physiological" in result.notes.lower() or "No claim" in result.notes


def test_resonance_two_tones():
    result = generate_and_analyze(
        frequencies_hz=[432.0, 440.0], sample_rate=22050, duration_s=1.0
    )
    assert len(result.frequencies_hz) == 2
    assert result.rms_amplitude > 0


def test_resonance_invalid_duration():
    with pytest.raises(ValueError):
        generate_and_analyze(duration_s=100)
