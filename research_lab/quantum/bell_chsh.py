"""
Quantum Experiment Laboratory — Bell / CHSH Inequality Simulation
Ascended Intelligence | Quantum–Consciousness Research Laboratory
Module: research_lab.quantum.bell_chsh

SCIENTIFIC CLASSIFICATION
-------------------------
Claim type: ESTABLISHED (quantum mechanics / Bell non-locality)

This module implements a classical Monte-Carlo simulation of the CHSH
inequality under the predictions of quantum mechanics for a maximally
entangled singlet state.

It does NOT claim that quantum mechanics proves, measures, or is caused by
consciousness, spiritual phenomena, or any non-physical entity.

References (standard physics literature):
- Bell, J.S. (1964). On the Einstein Podolsky Rosen Paradox.
- Clauser, J.F., Horne, M.A., Shimony, A., Holt, R.A. (1969). Proposed
  experiment to test local hidden-variable theories.
- Aspect, A. et al. experimental confirmations (1981–present).
- Textbook treatments (Nielsen & Chuang; Preskill notes; etc.).

All outputs are numerical simulation results only.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

import numpy as np


@dataclass
class CHSHResult:
    """Structured result of a CHSH simulation run."""

    experiment_id: str
    n_trials: int
    angles_deg: Dict[str, float]
    correlators: Dict[str, float]
    S: float
    classical_bound: float
    quantum_prediction: float
    tsirelson_bound: float
    violates_classical: bool
    seed: int
    runtime_seconds: float
    classification: str = "ESTABLISHED (quantum mechanics simulation)"
    limitations: str = (
        "This is a classical Monte-Carlo simulation of quantum predictions. "
        "It is not a physical quantum experiment on hardware and makes no "
        "claims about consciousness or spiritual phenomena."
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _angle_to_rad(deg: float) -> float:
    return np.deg2rad(deg)


def quantum_expectation(theta_a: float, theta_b: float) -> float:
    """
    Expectation value <A B> for the singlet state.
    <σ · a  σ · b> = -cos(θ_a - θ_b)
    """
    return -np.cos(theta_a - theta_b)


def simulate_chsh(
    n_trials: int = 100_000,
    angle_a1_deg: float = 0.0,
    angle_a2_deg: float = 90.0,
    angle_b1_deg: float = 45.0,
    angle_b2_deg: float = -45.0,
    seed: Optional[int] = None,
) -> CHSHResult:
    """
    Monte-Carlo simulation of CHSH correlators under quantum predictions.

    Default angles (A1=0°, A2=90°, B1=45°, B2=-45°) yield the Tsirelson
    bound |S| = 2√2 ≈ 2.828 under quantum mechanics for the singlet.

    Classical local-realistic theories satisfy |S| ≤ 2.

    This is pure quantum information / foundations. No consciousness claims.
    """
    if n_trials < 1_000:
        raise ValueError("n_trials must be ≥ 1000 for meaningful statistics")
    if n_trials > 5_000_000:
        raise ValueError("n_trials limited to 5e6 for resource control")

    if seed is None:
        seed = int(time.time() * 1000) % (2**31)

    rng = np.random.default_rng(seed)
    t0 = time.perf_counter()

    a1 = _angle_to_rad(angle_a1_deg)
    a2 = _angle_to_rad(angle_a2_deg)
    b1 = _angle_to_rad(angle_b1_deg)
    b2 = _angle_to_rad(angle_b2_deg)

    # Analytic quantum expectations for the singlet
    E11 = quantum_expectation(a1, b1)
    E12 = quantum_expectation(a1, b2)
    E21 = quantum_expectation(a2, b1)
    E22 = quantum_expectation(a2, b2)

    # CHSH combination that reaches the Tsirelson bound |S| = 2√2
    # for angles A1=0°, A2=90°, B1=45°, B2=-45°
    S_quantum = E11 + E12 + E21 - E22

    def sample_correlator(E: float, n: int) -> float:
        """Sample ±1 outcomes whose mean estimates the correlator E."""
        p_same = np.clip((1.0 + E) / 2.0, 0.0, 1.0)
        same = rng.random(n) < p_same
        outcomes = np.where(same, 1.0, -1.0)
        return float(np.mean(outcomes))

    corr = {
        "E(a1,b1)": sample_correlator(E11, n_trials),
        "E(a1,b2)": sample_correlator(E12, n_trials),
        "E(a2,b1)": sample_correlator(E21, n_trials),
        "E(a2,b2)": sample_correlator(E22, n_trials),
    }

    S_est = (
        corr["E(a1,b1)"]
        + corr["E(a1,b2)"]
        + corr["E(a2,b1)"]
        - corr["E(a2,b2)"]
    )

    runtime = time.perf_counter() - t0

    param_str = (
        f"{n_trials}-{angle_a1_deg}-{angle_a2_deg}-"
        f"{angle_b1_deg}-{angle_b2_deg}-{seed}"
    )
    exp_id = "chsh-" + hashlib.sha256(param_str.encode()).hexdigest()[:12]

    return CHSHResult(
        experiment_id=exp_id,
        n_trials=n_trials,
        angles_deg={
            "A1": angle_a1_deg,
            "A2": angle_a2_deg,
            "B1": angle_b1_deg,
            "B2": angle_b2_deg,
        },
        correlators=corr,
        S=float(S_est),
        classical_bound=2.0,
        quantum_prediction=float(S_quantum),
        tsirelson_bound=float(2 * np.sqrt(2)),
        violates_classical=abs(S_est) > 2.0,
        seed=seed,
        runtime_seconds=runtime,
    )


def run_demo() -> None:
    """CLI demonstration of the CHSH simulation."""
    print("=" * 64)
    print("CHSH / Bell Inequality Simulation (Quantum Predictions)")
    print("Classification: ESTABLISHED (standard quantum mechanics)")
    print("No claims are made about consciousness or spirituality.")
    print("=" * 64)

    result = simulate_chsh(n_trials=250_000, seed=42)
    print(json.dumps(result.to_dict(), indent=2))
    print()
    print(f"Estimated S          = {result.S:.4f}")
    print(f"Quantum prediction   = {result.quantum_prediction:.4f}")
    print(f"Tsirelson bound 2√2  = {result.tsirelson_bound:.4f}")
    print(f"Classical bound |S|  ≤ 2")
    print(f"Violates classical   : {result.violates_classical}")


if __name__ == "__main__":
    run_demo()
