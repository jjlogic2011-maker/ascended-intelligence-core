# README Claim Corrections — 2026-09-24

PATCH 01 corrected the following claims in `README.md`.

## 1. Framework / startup command
- Original: `uvicorn src.api.main:app --reload`
- Observed: Flask app at `api/app.py`; Dockerfile uses Gunicorn with `api.app:app`
- Tier: CITED

## 2. TABS percentage badge
- Original: `TABS Score 89%`
- Observed: no TABS implementation located
- Tier: NOT_AVAILABLE

## 3. TABS test count
- Original: `120+ adversarial tests`
- Observed: no executable TABS suite located
- Tier: ROADMAP

## 4. SHAPE implementation status
- Original: implied implemented
- Observed: documentation only (`docs/SHAPE_PROTOCOL.md`)
- Tier: SPECIFICATION

## 5. AIRI-DNA implementation status
- Original: implied implemented
- Observed: documentation only (`docs/AIRI_DNA.md`)
- Tier: SPECIFICATION

## 6. Living Ledger implementation status
- Original: "immutable repository"
- Observed: documentation only (`docs/TRUSTOS_ARCHITECTURE.md`)
- Tier: SPECIFICATION

## 7. Wasmer / Tenki runtime adapters
- Original: implied implemented
- Observed: no adapter source located
- Tier: ROADMAP

## 8. Reported 42% figure
- Original: cited as failure rate
- Observed: no denominator, numerator, commit, or raw report located
- Tier: NOT_AVAILABLE

## 9. "The Operating System for Trustworthy Intelligence"
- Original: presented as current state
- Observed: broader vision; current implementation is a minimal Flask service
- Tier: SPECIFICATION
