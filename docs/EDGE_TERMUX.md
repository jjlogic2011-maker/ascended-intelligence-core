# Edge execution — Termux (Android)

**Purpose:** Document sovereign/offline-capable run of the TrustOS kernel on-device.

## Requirements

- Android device with [Termux](https://termux.dev/)
- Network for initial `pkg` / `pip` only (runtime can be offline after install)
- Sufficient storage for Python + venv

## Steps (reference)

```bash
pkg update && pkg install python git
git clone https://github.com/jjlogic2011-maker/ascended-intelligence-core.git
cd ascended-intelligence-core
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export AICI_API_KEY=agent-demo-key
export AICI_LEDGER_PATH=$HOME/trustos_ledger.jsonl
python demo.py
# Optional API:
# pip install flask
# flask --app api.app run --host=127.0.0.1 --port=5000
```

## Verification

1. `demo.py` completes without cloud calls required for core ledger path.  
2. Ledger file grows under `AICI_LEDGER_PATH`.  
3. Optional: copy receipt JSON off-device and run `verify_export` on a laptop.

## Limits

- Not a hardened mobile MDM product.  
- Battery, process kill, and storage limits are device-specific.  
- Do not claim “certified air-gap product” without a formal test protocol.

## Evidence for claims

When asserting Termux success publicly, retain: device model, Termux version, commit SHA, and a redacted ledger tip hash.
