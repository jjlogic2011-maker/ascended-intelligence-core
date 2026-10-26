#!/usr/bin/env python3
"""Offline integrity export verifier CLI.

Usage:
  python scripts/verify_export_cli.py path/to/receipt.json

Exit 0 if export_hash matches canonical packet; non-zero otherwise.
Note: this checks integrity of the packet bytes, not external issuer authenticity.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from security.export import verify_export


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/verify_export_cli.py <receipt.json>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    packet = json.loads(path.read_text(encoding="utf-8"))
    ok = verify_export(packet)
    print("verify_export", ok)
    print("request_id", packet.get("request_id"))
    print("event_count", packet.get("event_count"))
h = packet.get("export_hash") or ""
    print("export_hash", (h[:16] + "…") if h else "missing")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
