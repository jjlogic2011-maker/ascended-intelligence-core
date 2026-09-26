#!/usr/bin/env bash
# Verify TrustOS kernel in one command.
# Runs pytest and TABS, prints a summary. Exits non-zero on failure.

set -e

echo "=== TrustOS Kernel Verification ==="
echo

echo "[1/3] pytest"
python -m pytest -q || { echo "FAILED: pytest"; exit 1; }
echo

echo "[2/3] TABS adversarial suite"
python -m security.tabs || { echo "FAILED: TABS"; exit 1; }
echo

echo "[3/3] Evidence bundle"
if [ -f evidence/kernel-verification-2026-09-25.json ]; then
    echo "Present: evidence/kernel-verification-2026-09-25.json"
else
    echo "Not present — run scripts/generate_kernel_evidence.py to create"
fi

echo
echo "=== Verification complete ==="
