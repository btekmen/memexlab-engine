#!/usr/bin/env python3
"""Summarize a local retrieval meter JSONL file. No network.

Reads the same record format ``memex meter`` writes. Default file is
``<vault>/.memex/meter.jsonl``. Override with ``--path``, ``MEMEX_METER_PATH``,
or ``meter_path:`` in the vault's governance.yml.

A missing file is an empty summary, not an error. ``hit`` stays null until an
eval fills it; those rows count as pending.

Usage:
  python3 scripts/meter_summary.py --vault ~/vault
  python3 scripts/meter_summary.py --path ~/vault/.memex/meter.jsonl --format json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "memex-cli" / "src"
if SRC.is_dir() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from memex_cli.meter import format_summary, resolve_path, summarize  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", default=os.environ.get("MEMEX_VAULT", "."),
                        help="vault root (default: MEMEX_VAULT or cwd)")
    parser.add_argument("--path", default=None,
                        help="meter JSONL (default: <vault>/.memex/meter.jsonl)")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    vault = Path(args.vault).expanduser()
    if not vault.is_dir():
        print(f"error: vault root is not a directory: {vault}", file=sys.stderr)
        print(json.dumps({"cmd": "meter-summary", "ok": False,
                          "error": "vault root is not a directory"}), file=sys.stderr)
        return 1
    try:
        path = resolve_path(vault, args.path)
        summary = summarize(path)
    except (ValueError, PermissionError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(json.dumps({"cmd": "meter-summary", "ok": False, "error": str(exc)}),
              file=sys.stderr)
        return 1
    event = {"cmd": "meter-summary", "path": str(path), "ok": True, **summary}
    print(json.dumps(event, ensure_ascii=False), file=sys.stderr)
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(format_summary(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
