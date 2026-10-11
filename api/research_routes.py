"""QCR Lab research API routes — additive to TrustOS core.

All scientific endpoints are clearly labeled. Quantum endpoints run
classical Monte-Carlo simulations only. No consciousness claims.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

research_bp = Blueprint("research", __name__)

# Lazy imports so core service still starts without scientific deps
def _get_research():
    try:
        from research.experiments import run_experiment, STORE
        from research.evidence import EvidenceRegistry
        return run_experiment, STORE, EvidenceRegistry
    except ImportError as exc:
        return None, None, None


@research_bp.route("/api/research/health")
def research_health():
    run_experiment, STORE, EvidenceRegistry = _get_research()
    available = run_experiment is not None
    return jsonify(
        {
            "status": "ok" if available else "degraded",
            "scientific_modules": available,
            "message": (
                "QCR Lab research layer ready"
                if available
                else "Install requirements-scientific.txt (numpy) to enable simulations"
            ),
            "integrity": "See docs/SCIENTIFIC_INTEGRITY.md — no consciousness claims",
        }
    )


@research_bp.route("/api/research/claims")
def research_claims():
    run_experiment, STORE, EvidenceRegistry = _get_research()
    if EvidenceRegistry is None:
        return jsonify({"error": "scientific modules unavailable"}), 503
    domain = request.args.get("domain")
    evidence_class = request.args.get("evidence_class")
    reg = EvidenceRegistry()
    claims = reg.list_claims(domain=domain, evidence_class=evidence_class)
    return jsonify({"count": len(claims), "claims": claims})


@research_bp.route("/api/experiments/quantum", methods=["POST"])
def experiments_quantum():
    run_experiment, STORE, EvidenceRegistry = _get_research()
    if run_experiment is None:
        return jsonify({"error": "numpy/scientific modules not installed"}), 503
    data = request.get_json(silent=True) or {}
    n_trials = data.get("n_trials", 10_000)
    seed = data.get("seed", 42)
    record = run_experiment("quantum", {"n_trials": n_trials, "seed": seed})
    return jsonify(record), 200 if record["status"] == "completed" else 400


@research_bp.route("/api/experiments/resonance", methods=["POST"])
def experiments_resonance():
    run_experiment, STORE, EvidenceRegistry = _get_research()
    if run_experiment is None:
        return jsonify({"error": "numpy/scientific modules not installed"}), 503
    data = request.get_json(silent=True) or {}
    record = run_experiment(
        "resonance",
        {
            "frequencies_hz": data.get("frequencies_hz"),
            "sample_rate": data.get("sample_rate", 44100),
            "duration_s": data.get("duration_s", 1.0),
        },
    )
    return jsonify(record), 200 if record["status"] == "completed" else 400


@research_bp.route("/api/experiments/<experiment_id>")
def experiment_get(experiment_id):
    run_experiment, STORE, EvidenceRegistry = _get_research()
    if STORE is None:
        return jsonify({"error": "scientific modules unavailable"}), 503
    rec = STORE.get(experiment_id)
    if rec is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(rec)


@research_bp.route("/api/experiments")
def experiments_list():
    run_experiment, STORE, EvidenceRegistry = _get_research()
    if STORE is None:
        return jsonify({"error": "scientific modules unavailable"}), 503
    limit = min(int(request.args.get("limit", 20)), 100)
    return jsonify({"experiments": STORE.list_recent(limit=limit)})
