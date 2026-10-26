#!/usr/bin/env bash
# TrustOS Assessment Grade Harness (A1) — FAIL CLOSED
# Mandatory evidence missing => non-zero exit.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ARTIFACTS="$ROOT/artifacts/assessment"
mkdir -p "$ARTIFACTS"
LEDGER_PATH="$ARTIFACTS/assessment_ledger.jsonl"
RECEIPT_PATH="$ARTIFACTS/sample_receipt.json"
rm -f "$LEDGER_PATH" "$RECEIPT_PATH"

export AICI_LEDGER_PATH="$LEDGER_PATH"
export AICI_API_KEY="${AICI_API_KEY:-agent-demo-key}"

echo "=============================================="
echo " TrustOS A1 Assessment Harness (fail-closed)"
echo "=============================================="

echo ""
echo "=== 1. Unit tests (must pass) ==="
python -m pytest -q --tb=line -o addopts=""

echo ""
echo "=== 2. Coverage on security/ and api/ (must run; no || true) ==="
python -m pytest -q -o addopts="" --cov=security --cov=api --cov-report=term-missing

echo ""
echo "=== 3. Persistent ledger receipt (write, restart load, verify) ==="
python scripts/persistence_receipt.py --ledger "$LEDGER_PATH"
test -f "$LEDGER_PATH"

echo ""
echo "=== 4. Standalone export CLI (separate process + tamper fails) ==="
python scripts/export_receipt_build.py --ledger "$LEDGER_PATH" --out "$RECEIPT_PATH"
python scripts/verify_export_cli.py "$RECEIPT_PATH"
# Tamper must fail
python -c "
import json, pathlib, subprocess, sys
p = pathlib.Path(r'''$RECEIPT_PATH''')
data = json.loads(p.read_text())
data['events'][0]['event_type'] = 'TAMPERED'
tampered = p.with_name('tampered_receipt.json')
tampered.write_text(json.dumps(data))
r = subprocess.run([sys.executable, 'scripts/verify_export_cli.py', str(tampered)])
assert r.returncode != 0, 'tampered receipt must fail verification'
print('tamper_rejected_ok')
"

echo ""
echo "=== 5. Concurrent claim receipt (one winner) ==="
python scripts/concurrency_claim_receipt.py

echo ""
echo "=== 6. Demo (informational; durable path proven in step 3) ==="
if [[ -f demo.py ]]; then
  python demo.py || { echo "demo failed"; exit 1; }
fi

echo ""
echo "=============================================="
echo " A1 HARNESS PASSED"
echo " ledger:  $LEDGER_PATH"
echo " receipt: $RECEIPT_PATH"
echo " See docs/LIMITATIONS.md — offline hash ≠ external authenticity."
echo "=============================================="
