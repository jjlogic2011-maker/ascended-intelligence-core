#!/usr/bin/env bash
# TrustOS Assessment Grade Harness (A1)
# Run from repo root after: pip install -r requirements.txt -r requirements-dev.txt
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

LEDGER_PATH="${AICI_LEDGER_PATH:-$ROOT/artifacts/assessment_ledger.jsonl}"
mkdir -p "$(dirname "$LEDGER_PATH")"
export AICI_LEDGER_PATH="$LEDGER_PATH"
export AICI_API_KEY="${AICI_API_KEY:-agent-demo-key}"

echo "=============================================="
echo " TrustOS Assessment Grade Harness (A1)"
echo "=============================================="

echo ""
echo "=== 1. Unit tests (no hard --cov required) ==="
python -m pytest -q --tb=line

echo ""
echo "=== 2. Coverage on security/ and api/ (informational) ==="
if python -c "import pytest_cov" 2>/dev/null; then
  python -m pytest --cov=security --cov=api --cov-report=term-missing -q || true
else
  echo "pytest-cov not installed; skip coverage (CI should still run it)"
fi

echo ""
echo "=== 3. Demo governed path ==="
if [[ -f demo.py ]]; then
  python demo.py
else
  echo "WARN: demo.py not found"
fi

echo ""
echo "=== 4. Ledger integrity (if ledger file exists) ==="
if [[ -f "$LEDGER_PATH" ]]; then
  python -c "
from security.ledger import load_ledger
ok, errs = load_ledger(r'''$LEDGER_PATH''').verify()
print('ledger_ok', ok)
if not ok:
    raise SystemExit('LEDGER VERIFY FAILED: ' + str(errs))
"
else
  echo "No ledger at $LEDGER_PATH yet (demo may use in-memory only)"
fi

echo ""
echo "=== 5. Offline export verifier self-check ==="
python -c "
from security.export import generate_export, verify_export
from security.ledger import LivingLedger

led = LivingLedger()
led.append(event_type='ASSESSMENT', actor='harness', agent='test', request_id='assess-1', artifact_id='selfcheck')
pkt = generate_export(led, 'assess-1')
assert pkt is not None
assert verify_export(pkt) is True
# Tamper
pkt['events'][0]['event_type'] = 'TAMPERED'
assert verify_export(pkt) is False
print('export_verify_ok True')
"

echo ""
echo "=============================================="
echo " A1 CANDIDATE: tests + export verify path OK"
echo " Review docs/LIMITATIONS.md before any claim."
echo "=============================================="
