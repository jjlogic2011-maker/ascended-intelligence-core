#!/usr/bin/env python3
import base64
from pathlib import Path
root = Path(__file__).resolve().parents[1]
b64 = (root / "api" / "app.py.b64").read_text().replace("\n", "").strip()
target = root / "api" / "app.py"
target.write_bytes(base64.b64decode(b64))
print("restored", target, "bytes", target.stat().st_size)
