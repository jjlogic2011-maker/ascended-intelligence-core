#!/usr/bin/env python3
"""Assemble api/app.py from api/_assembly_parts/*.part (CAS + AICI_LEDGER_PATH)."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
parts_dir = root / "api" / "_assembly_parts"
parts = sorted(parts_dir.glob("*.part"), key=lambda p: int(p.stem))
if not parts:
    raise SystemExit("no parts found")
text = "".join(p.read_text(encoding="utf-8") for p in parts)
out = root / "api" / "app.py"
out.write_text(text, encoding="utf-8")
print("assembled", out, "bytes", len(text.encode()), "parts", len(parts))
assert "claim_status" in text
assert "AICI_LEDGER_PATH" in text
assert text.count("@app.route") >= 10
