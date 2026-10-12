"""
Resonance Laboratory — controlled audio signal generation and spectral analysis.

SCIENTIFIC CLASSIFICATION
-------------------------
- Signal generation and FFT analysis: ESTABLISHED (standard digital signal processing)
- Any claim that 432 Hz vs 440 Hz produces established physiological or healing effects:
  SPECULATIVE / NOT CLAIMED

This module generates pure tones and computes spectral characteristics only.
It does not assert medical, psychological, or spiritual outcomes.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class ResonanceResult:
    experiment_id: str
    sample_rate: int
    duration_sec: float
    frequencies_hz: List[float]
    amplitudes: List[float]
    peak_frequencies_hz: List[float]
    peak_magnitudes: List[float]
    spectral_centroid_hz: float
    rms: float
    seed: int
    runtime_seconds: float
    classification: str = (
        "ESTABLISHED (DSP signal generation & spectral analysis); "
        "physiological/healing effects of 432 vs 440 Hz: SPECULATIVE / NOT CLAIMED"
    )
    limitations: str = (
        "Numerical simulation only. No physiological measurement is performed. "
        "No claim is made that 432 Hz or 440 Hz produces healing or consciousness effects."
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generate_tone(
    frequency_hz: float,
    duration_sec: float = 1.0,
    sample_rate: int = 44100,
    amplitude: float = 0.5,
    seed: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate a pure sine tone. Returns (time_axis, signal)."""
    if frequency_hz <= 0 or frequency_hz >= sample_rate / 2:
        raise ValueError("frequency_hz must be in (0, Nyquist)")
    if duration_sec <= 0 or duration_sec > 30:
        raise ValueError("duration_sec must be in (0, 30]")
    n = int(sample_rate * duration_sec)
    t = np.arange(n) / sample_rate
    if seed is not None:
        rng = np.random.default_rng(seed)
        phase = rng.uniform(0, 2 * np.pi)
    else:
        phase = 0.0
    signal = amplitude * np.sin(2 * np.pi * frequency_hz * t + phase)
    return t, signal


def spectral_peaks(
    signal: np.ndarray,
    sample_rate: int,
    n_peaks: int = 3,
) -> Tuple[List[float], List[float], float]:
    """Return top peak frequencies (Hz), magnitudes, and spectral centroid."""
    n = len(signal)
    windowed = signal * np.hanning(n)
    spectrum = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    spectrum[0] = 0.0
    idx = np.argsort(spectrum)[::-1][:n_peaks]
    peak_freqs = [float(freqs[i]) for i in idx]
    peak_mags = [float(spectrum[i]) for i in idx]
    total = spectrum.sum() + 1e-12
    centroid = float((freqs * spectrum).sum() / total)
    return peak_freqs, peak_mags, centroid


def compare_432_vs_440(
    duration_sec: float = 1.0,
    sample_rate: int = 44100,
    seed: int = 432,
) -> Dict[str, Any]:
    """Generate 432 Hz and 440 Hz tones and compare spectral features. Physiological claims remain SPECULATIVE."""
    t0 = time.perf_counter()
    results = {}
    for f in (432.0, 440.0):
        _, sig = generate_tone(f, duration_sec, sample_rate, amplitude=0.5, seed=seed)
        peaks, mags, centroid = spectral_peaks(sig, sample_rate)
        results[str(f)] = {
            "target_hz": f,
            "peak_frequencies_hz": peaks,
            "peak_magnitudes": mags,
            "spectral_centroid_hz": centroid,
            "rms": float(np.sqrt(np.mean(sig**2))),
        }
    runtime = time.perf_counter() - t0
    param = f"432v440-{duration_sec}-{sample_rate}-{seed}"
    exp_id = "res-" + hashlib.sha256(param.encode()).hexdigest()[:12]
    return {
        "experiment_id": exp_id,
        "comparison": results,
        "runtime_seconds": runtime,
        "classification": (
            "ESTABLISHED (DSP); any healing/consciousness effect of 432 vs 440: SPECULATIVE"
        ),
        "limitations": (
            "This comparison is spectral only. No physiological or clinical claim is made."
        ),
    }


def run_resonance_experiment(
    frequencies_hz: Optional[List[float]] = None,
    duration_sec: float = 1.0,
    sample_rate: int = 44100,
    seed: int = 42,
) -> ResonanceResult:
    """Multi-frequency resonance experiment with spectral analysis."""
    if frequencies_hz is None:
        frequencies_hz = [432.0, 440.0]
    if len(frequencies_hz) > 8:
        raise ValueError("Max 8 frequencies per run")

    t0 = time.perf_counter()
    mixed = None
    amplitudes = []
    for i, f in enumerate(frequencies_hz):
        amp = 0.5 / len(frequencies_hz)
        amplitudes.append(amp)
        _, sig = generate_tone(f, duration_sec, sample_rate, amplitude=amp, seed=seed + i)
        mixed = sig if mixed is None else mixed + sig

    peaks, mags, centroid = spectral_peaks(mixed, sample_rate, n_peaks=min(5, len(frequencies_hz) + 1))
    rms = float(np.sqrt(np.mean(mixed**2)))
    runtime = time.perf_counter() - t0

    param = f"{frequencies_hz}-{duration_sec}-{sample_rate}-{seed}"
    exp_id = "res-" + hashlib.sha256(param.encode()).hexdigest()[:12]

    return ResonanceResult(
        experiment_id=exp_id,
        sample_rate=sample_rate,
        duration_sec=duration_sec,
        frequencies_hz=list(frequencies_hz),
        amplitudes=amplitudes,
        peak_frequencies_hz=peaks,
        peak_magnitudes=mags,
        spectral_centroid_hz=centroid,
        rms=rms,
        seed=seed,
        runtime_seconds=runtime,
    )


def run_demo() -> None:
    print("=" * 64)
    print("Resonance Laboratory — 432 Hz vs 440 Hz spectral comparison")
    print("DSP: ESTABLISHED | Physiological effects: SPECULATIVE / NOT CLAIMED")
    print("=" * 64)
    comp = compare_432_vs_440(duration_sec=0.5, seed=432)
    print("experiment_id:", comp["experiment_id"])
    for k, v in comp["comparison"].items():
        print(f"  {k} Hz -> peaks≈{v['peak_frequencies_hz'][:2]}, centroid={v['spectral_centroid_hz']:.2f}")
    print(comp["classification"])
    r = run_resonance_experiment([432.0, 440.0], duration_sec=0.5, seed=42)
    print("Mixed S experiment_id:", r.experiment_id, "rms:", round(r.rms, 4))


if __name__ == "__main__":
    run_demo()
