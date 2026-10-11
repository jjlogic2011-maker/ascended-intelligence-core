"""QCR Lab research modules — classical simulations and evidence tooling.

See docs/SCIENTIFIC_INTEGRITY.md. No module claims quantum mechanics
proves consciousness or frequency-based healing.
"""

from .quantum import run_chsh_simulation
from .resonance import generate_and_analyze
from .evidence import EvidenceRegistry
from .experiments import ExperimentStore, run_experiment

__all__ = [
    "run_chsh_simulation",
    "generate_and_analyze",
    "EvidenceRegistry",
    "ExperimentStore",
    "run_experiment",
]
