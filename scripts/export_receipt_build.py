#!/usr/bin/env python3
"""Build a standalone JSON integrity export from a ledger file."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from security.export import generate_export
from security.ledger import load_ledger


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--ledger", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--request-id", default="persist-1")
    args = p.parse_args()

    led = load_ledger(args.ledger)
    packet = generate_export(led, args.request_id)
    if packet is None:
        print("no_events_for_request_id", args.request_id)
        return 1
    Path(args.out).write_text(json.dumps(packet, indent=2), encoding="utf-8")
    print("export_written", args.out, "hash", packet["export_hash"][:16])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
