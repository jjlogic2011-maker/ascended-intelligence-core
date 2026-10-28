#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "=== pytest ==="
python -m pytest -q --tb=line -o addopts=""
echo "=== race boundary (if present) ==="
python -m pytest -q tests/adversarial/test_race_001_boundary.py -o addopts="" || python -m pytest -q tests/adversarial/ -o addopts=""
echo "ASSESSMENT HARNESS OK (reference kernel)"
