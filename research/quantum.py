"""Classical Monte-Carlo simulation of the CHSH Bell inequality.

This is a numerical experiment, not a claim about physical quantum hardware
or consciousness. Results are labeled SPECULATIVE / PRELIMINARY as appropriate.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class CHSHResult:
    experiment_id: str
    n_trials: int
    settings: List[Tuple[float, float]]
    correlators: Dict[str, float]
    S: float
    classical_bound: float
    quantum_bound: float
    violates_classical: bool
    method: str
    evidence_class: str
    notes: str
    seed: Optional[int]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _angle_to_projector(theta: float) -> np.ndarray:
    """Simple 2-outcome observable for angle theta (Pauli-like)."""
    c, s = np.cos(theta), np.sin(theta)
    # Observable = cos(theta)*Z + sin(theta)*X in computational basis
    return np.array([[c, s], [s, -c]], dtype=float)


def run_chsh_simulation(
    n_trials: int = 10_000,
    seed: Optional[int] = 42,
    angles: Optional[List[Tuple[float, float]]] = None,
) -> CHSHResult:
    """
    Classical Monte-Carlo CHSH experiment.

    Uses a shared random bit (classical common cause) plus local randomness
    to illustrate the classical bound |S| <= 2. A separate pure-quantum
    analytic value is reported for comparison only.

    Evidence classification: PRELIMINARY (numerical illustration).
    """
    if n_trials < 100 or n_trials > 1_000_000:
        raise ValueError("n_trials must be between 100 and 1_000_000")

    rng = np.random.default_rng(seed)

    # Standard CHSH angle set (radians)
    if angles is None:
        # A0=0, A1=pi/4, B0=pi/8, B1=-pi/8  (common textbook choice)
        a0, a1 = 0.0, np.pi / 4
        b0, b1 = np.pi / 8, -np.pi / 8
        settings = [(a0, b0), (a0, b1), (a1, b0), (a1, b1)]
    else:
        settings = angles

    # Classical simulation: shared random bit lambda + local deterministic responses
    # This cannot exceed |S|=2.
    lambdas = rng.integers(0, 2, size=n_trials)

    def response_a(theta: float, lam: np.ndarray) -> np.ndarray:
        # Deterministic local strategy (toy)
        return np.where(lam == 0, 1, -1)

    def response_b(theta: float, lam: np.ndarray) -> np.ndarray:
        return np.where(lam == 0, 1, -1)

    correlators = {}
    labels = ["A0B0", "A0B1", "A1B0", "A1B1"]
    for (theta_a, theta_b), label in zip(settings, labels):
        a = response_a(theta_a, lambdas)
        b = response_b(theta_b, lambdas)
        correlators[label] = float(np.mean(a * b))

    # CHSH combination (one conventional ordering)
    S = (
        correlators["A0B0"]
        + correlators["A0B1"]
        + correlators["A1B0"]
        - correlators["A1B1"]
    )

    classical_bound = 2.0
    quantum_bound = 2 * np.sqrt(2)  # Tsirelson bound ≈ 2.828

    # Stable experiment id from parameters
    payload = json.dumps(
        {"n": n_trials, "seed": seed, "settings": settings}, sort_keys=True
    )
    exp_id = hashlib.sha256(payload.encode()).hexdigest()[:16]

    return CHSHResult(
        experiment_id=exp_id,
        n_trials=n_trials,
        settings=[(float(a), float(b)) for a, b in settings],
        correlators=correlators,
        S=float(S),
        classical_bound=classical_bound,
        quantum_bound=float(quantum_bound),
        violates_classical=abs(S) > classical_bound + 1e-9,
        method="classical_monte_carlo_shared_randomness",
        evidence_class="PRELIMINARY",
        notes=(
            "Classical local-hidden-variable simulation. "
            "|S| cannot exceed 2 under these assumptions. "
            "Quantum Tsirelson bound is shown for comparison only. "
            "This is not a claim about physical quantum hardware or consciousness."
        ),
        seed=seed,
    )
