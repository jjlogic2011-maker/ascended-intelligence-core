# Known limitations

Inspected on main `28e2dd04f17b8e3e4181b3d8a91326664012c1b1`.

## Approval claim is not cross-process

While `PendingStore.claim_status` provides atomic SQLite cross-process safety, the current API approval paths (`_do_approve`, `_do_deny` in `api/app.py`) still rely on a process-local `threading.RLock()`. The next engineering priority is wiring the API layer directly to `claim_status` to prevent race conditions in multi-process deployments.

What is true today:

- `security/pending_store.py` implements `PendingStore.claim_status` with `BEGIN IMMEDIATE` and `UPDATE ... WHERE status = from_status`. That is the cross-process claim. Its own `threading.RLock` does not protect another process.
- `api/app.py` holds module-level `PENDING_LOCK = threading.RLock()` around `_do_approve`, `_do_deny`, and `_close_malformed_approval`.
- Those handlers then call `store.update_status(...)`. They do not call `claim_status`.
- One process is serialized. Two processes, or two Gunicorn workers, can both pass the in-process lock and race on the same pending id.

This file is documentation only. It does not change the approval path.
