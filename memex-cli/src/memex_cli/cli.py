"""memex — universal contract: dry-run by default, `--apply` writes, one JSON
event per invocation to stderr, exit 0 on success / 1 on error."""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__
from .ingest_url import ingest_url
from .vault import Vault


def _emit(cmd: str, result: dict) -> None:
    event = {"cmd": cmd, **result}
    print(json.dumps(event, ensure_ascii=False), file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="memex", description=__doc__)
    parser.add_argument("--version", action="version", version=f"memex {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="bring sources into the vault")
    ingest_sub = ingest.add_subparsers(dest="source", required=True)

    url_p = ingest_sub.add_parser("url", help="capture a public web page into the write dir")
    url_p.add_argument("url", help="the page to capture")
    url_p.add_argument("--vault", default=os.environ.get("MEMEX_VAULT", "."),
                       help="vault root (or set MEMEX_VAULT; default: cwd)")
    url_p.add_argument("--apply", action="store_true",
                       help="write the note (default: dry-run preview)")
    url_p.add_argument("--force", action="store_true",
                       help="re-capture even if this URL was ingested before")

    args = parser.parse_args(argv)

    if args.command == "ingest" and args.source == "url":
        try:
            vault = Vault(args.vault)
            result = ingest_url(vault, args.url, apply=args.apply, force=args.force)
        except (ValueError, PermissionError) as e:
            _emit("ingest-url", {"action": "error", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        _emit("ingest-url", result)
        if not result["ok"]:
            print(f"error: {result['action']} for {args.url}")
            return 1
        if result["action"] == "skip-duplicate":
            print(f"already captured: {result['note']} (use --force to re-capture)")
        elif result["applied"]:
            print(f"captured: {result['note']}")
        else:
            print(f"dry-run: would write {result['note']} "
                  f"({result['chars']} chars from \"{result['title']}\"). "
                  f"Use --apply to write.")
        return 0

    parser.error("unknown command")
    return 1


if __name__ == "__main__":
    sys.exit(main())
