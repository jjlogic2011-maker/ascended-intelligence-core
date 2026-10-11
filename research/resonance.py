"""Controlled audio-frequency waveform generation and spectral analysis.

Generates pure tones (e.g. 432 Hz and 440 Hz) and returns numerical
waveform + FFT characteristics. No physiological or healing claims.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class ResonanceResult:
    experiment_id: str
    frequencies_hz: List[float]
    sample_rate: int
    duration_s: float
    peak_frequencies: List[float]
    peak_magnitudes: List[float]
    rms_amplitude: float
    method: str
    evidence_class: str
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generate_and_analyze(
    frequencies_hz: Optional[List[float]] = None,
    sample_rate: int = 44100,
    duration_s: float = 1.0,
    amplitude: float = 0.5,
) -> ResonanceResult:
    """
    Generate a sum of pure sinusoids and compute basic spectral peaks.

    Default frequencies: 432 Hz and 440 Hz (reference comparison only).
    Evidence classification: ESTABLISHED for the numerical signal itself;
    any biological interpretation remains SPECULATIVE and is not asserted here.
    """
    if frequencies_hz is None:
        frequencies_hz = [432.0, 440.0]

    if sample_rate < 8000 or sample_rate > 192000:
        raise ValueError("sample_rate out of supported range")
    if duration_s <= 0 or duration_s > 30:
        raise ValueError("duration_s must be in (0, 30]")

    t = np.linspace(0, duration_s, int(sample_rate * duration_s), endpoint=False)
    signal = np.zeros_like(t)
    for f in frequencies_hz:
        signal += amplitude * np.sin(2 * np.pi * f * t)

    # FFT magnitude spectrum (positive frequencies)
    n = len(signal)
    spectrum = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    magnitude = np.abs(spectrum)

    # Simple peak picking: local maxima above a threshold
    threshold = 0.1 * magnitude.max()
    peaks_idx = []
    for i in range(1, len(magnitude) - 1):
        if magnitude[i] > magnitude[i - 1] and magnitude[i] > magnitude[i + 1]:
            if magnitude[i] >= threshold:
                peaks_idx.append(i)

    # Keep top peaks by magnitude
    peaks_idx = sorted(peaks_idx, key=lambda i: magnitude[i], reverse=True)[:8]
    peak_frequencies = [float(freqs[i]) for i in peaks_idx]
    peak_magnitudes = [float(magnitude[i]) for i in peaks_idx]

    rms = float(np.sqrt(np.mean(signal ** 2)))

    payload = json.dumps(
        {"freqs": frequencies_hz, "sr": sample_rate, "dur": duration_s},
        sort_keys=True,
    )
    exp_id = hashlib.sha256(payload.encode()).hexdigest()[:16]

    return ResonanceResult(
        experiment_id=exp_id,
        frequencies_hz=[float(f) for f in frequencies_hz],
        sample_rate=sample_rate,
        duration_s=duration_s,
        peak_frequencies=peak_frequencies,
        peak_magnitudes=peak_magnitudes,
        rms_amplitude=rms,
        method="numpy_sinusoid_sum_plus_rfft",
        evidence_class="ESTABLISHED",
        notes=(
            "Numerical generation and FFT of pure tones. "
            "No claim is made about physiological, psychological, or healing effects. "
            "Any such interpretation is SPECULATIVE and outside this module."
        ),
    )
