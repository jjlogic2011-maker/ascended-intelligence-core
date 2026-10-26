#!/usr/bin/env python3
"""Offline integrity export verifier CLI.

Usage:
  python scripts/verify_export_cli.py path/to/receipt.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running from repo root
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
    print("export_hash", packet.get("export_hash", "")[:16] + "…")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
