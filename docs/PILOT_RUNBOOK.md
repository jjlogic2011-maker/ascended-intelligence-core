# TrustOS Pilot Runbook

## Goal

In 30–90 days, prove one consequential agent path:

1. Requires human approval before execute  
2. Denial is recorded on the Living Ledger  
3. Integrity export verifies offline  
4. Limitations are acknowledged in writing  

## Prerequisites

- Python 3.10+
- Git
- Ability to set environment variables
- Optional: Termux for edge demo (see `docs/EDGE_TERMUX.md`)

## Install

```bash
git clone https://github.com/jjlogic2011-maker/ascended-intelligence-core.git
cd ascended-intelligence-core
git checkout main && git pull
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
```

## Assessment harness

```bash
chmod +x scripts/assessment_grade.sh
./scripts/assessment_grade.sh
```

Expect: pytest green, export self-check OK. Coverage is informational if pytest-cov is present.

## API (local)

```bash
export AICI_API_KEY="agent-demo-key"
export AICI_LEDGER_PATH="$(pwd)/artifacts/pilot_ledger.jsonl"
flask --app api.app run --host=127.0.0.1 --port=5000
```

Exercise approve/deny flows per current API routes; export via `/export/<request_id>` when available.

## Offline export verify

```python
from security.export import verify_export
import json
with open("receipt.json") as f:
    packet = json.load(f)
print(verify_export(packet))
```

## Success criteria (sign-off)

| # | Criterion | Pass? |
|---|-----------|-------|
| 1 | Assessment harness green | |
| 2 | One approved action leaves ledger events | |
| 3 | One denial leaves ledger events | |
| 4 | Export for a request_id verifies offline | |
| 5 | Customer signed `docs/LIMITATIONS.md` understanding | |

## Support during pilot

- Channel: agreed email / calendar office hours  
- Scope: install, mapping one agent path, export interpretation  
- Out of scope: SOC2 attestation, full GRC replacement, 24×7 unless contracted  

## Exit

- Continue to Kernel Support annual, or  
- End pilot with written findings; no forced upsell  
