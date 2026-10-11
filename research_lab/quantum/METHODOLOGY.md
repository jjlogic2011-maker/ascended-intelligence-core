# Quantum Experiment Laboratory — Methodology

## Module: Bell / CHSH Inequality Simulation

**Classification of the underlying physics claim:** ESTABLISHED  
(Bell non-locality / CHSH inequality is one of the most thoroughly tested results in quantum mechanics.)

**Classification of any link to consciousness:** SPECULATIVE / NOT CLAIMED  
This laboratory does **not** assert that quantum mechanics proves, measures, or is caused by consciousness, spiritual phenomena, or universal frequency-based healing.

### Hypothesis
Under the predictions of quantum mechanics for a maximally entangled singlet state, the CHSH correlator combination |S| can reach the Tsirelson bound 2√2 ≈ 2.828, thereby violating the classical local-realistic bound |S| ≤ 2.

### Method
- Analytic quantum expectation values for the singlet: ⟨A B⟩ = −cos(θ_A − θ_B)
- Monte-Carlo sampling of ±1 outcomes consistent with those correlators
- Default angles (A1=0°, A2=90°, B1=45°, B2=−45°) chosen to achieve the maximum quantum violation
- Resource limits: 1 000 ≤ n_trials ≤ 5 000 000

### Controls & Limitations
- This is a **classical simulation** of quantum predictions, not a physical quantum experiment on hardware.
- Statistical fluctuation is present; larger n_trials reduce sampling error.
- Negative findings (failure to exceed |S| = 2 under altered angles) are valid and reported.

### Reproduction
```bash
python -m research_lab.quantum.bell_chsh
```

### Provenance
All results include experiment_id (content hash of parameters + seed), seed, runtime, and explicit classification / limitations strings.
