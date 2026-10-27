#!/usr/bin/env python3
"""Assemble api/app.py from api/_app_parts/*.b64 (CAS + desk wire)."""
import base64
from pathlib import Path
root = Path(__file__).resolve().parents[1]
parts_dir = root / "api" / "_app_parts"
parts = sorted(parts_dir.glob("*.b64"), key=lambda p: int(p.stem))
if not parts:
    raise SystemExit("no parts")
blob = "".join(p.read_text().strip() for p in parts)
data = base64.b64decode(blob)
out = root / "api" / "app.py"
out.write_bytes(data)
assert b"claim_status" in data
print("assembled", out, "bytes", len(data))
