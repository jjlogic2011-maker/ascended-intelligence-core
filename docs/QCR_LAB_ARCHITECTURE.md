# QCR Lab Architecture (AI-QCR-2026-001)

## Relationship to TrustOS Core

The Quantum–Consciousness Research Laboratory is an **additive research layer** on top of the existing TrustOS governance kernel. It does not replace SHAPE, Living Ledger, AIRI-DNA, or human gates.

```
ascended-intelligence-core/
├── api/app.py              # existing Flask governance API (preserved)
├── security/               # existing TrustOS (preserved)
├── research/               # NEW scientific modules
│   ├── __init__.py
│   ├── quantum.py          # classical Bell/CHSH simulations
│   ├── resonance.py        # controlled waveform + spectral analysis
│   ├── neuroscience.py     # public EEG dataset helpers (stub)
│   ├── evidence.py         # claim/paper registry
│   └── experiments.py      # experiment runner + result store
├── docs/SCIENTIFIC_INTEGRITY.md
└── requirements-scientific.txt  # optional extras
```

## API Surface (additive)

- `GET  /api/research/health`
- `POST /api/experiments/quantum`
- `POST /api/experiments/resonance`
- `GET  /api/experiments/{id}`
- `GET  /api/experiments/{id}/results`
- `GET  /api/research/claims`
- `GET  /api/ledger` (re-uses existing Living Ledger)

All new routes remain under the same authentication and governance controls where appropriate.

## Design Rules

1. Optional scientific dependencies never break the minimal Flask runtime.
2. Every numerical result carries an explicit simulation label and evidence classification.
3. Results are persisted with timestamps and linked to Living Ledger events.
