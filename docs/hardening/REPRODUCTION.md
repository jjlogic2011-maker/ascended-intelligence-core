# Reproduction

## Repository

```text
https://github.com/jjlogic2011-maker/ascended-intelligence-core
main @ b7c59fab1ec688e7d9a62ee2fa83b83ebc15e493
```

## Environment (this audit)

- Platform: Linux
- Python: 3.12.x (sandbox)
- Flask: **not installed** → integration tests fail at collection
- pytest: available

## Commands run

```bash
git fetch origin && git checkout main && git pull
git rev-parse HEAD
python3 -m pytest tests/unit -q -o addopts=
python3 -m security.tabs
python3 -m pytest tests/unit/test_pending_store.py -q -o addopts=
```

## Topology note

SQLite pending store supports multiple processes on one host sharing one DB file.
It does **not** support arbitrary multi-host deployment without a networked database.
