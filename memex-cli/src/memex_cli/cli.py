"""memex — universal contract: dry-run by default, `--apply` writes, one JSON
event per invocation to stderr, exit 0 on success / 1 on error."""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__
from .ingest_kindle import ingest_kindle
from .ingest_readwise import ingest_readwise
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

    kindle_p = ingest_sub.add_parser("kindle", help="import Kindle 'My Clippings.txt' highlights")
    kindle_p.add_argument("file", help="path to My Clippings.txt (or an export in the same format)")
    kindle_p.add_argument("--vault", default=os.environ.get("MEMEX_VAULT", "."),
                          help="vault root (or set MEMEX_VAULT; default: cwd)")
    kindle_p.add_argument("--apply", action="store_true",
                          help="write/append notes (default: dry-run preview)")

    rw_p = ingest_sub.add_parser("readwise", help="incremental import from the Readwise export API")
    rw_p.add_argument("--vault", default=os.environ.get("MEMEX_VAULT", "."),
                      help="vault root (or set MEMEX_VAULT; default: cwd)")
    rw_p.add_argument("--since", default=None,
                      help="ISO date/time override for the incremental cursor")
    rw_p.add_argument("--apply", action="store_true",
                      help="write/append notes (default: dry-run preview)")

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

    if args.command == "ingest" and args.source == "kindle":
        try:
            vault = Vault(args.vault)
            result = ingest_kindle(vault, args.file, apply=args.apply)
        except FileNotFoundError:
            _emit("ingest-kindle", {"action": "error", "error": "file not found", "ok": False})
            print(f"error: no such file: {args.file}", file=sys.stderr)
            return 1
        except (ValueError, PermissionError) as e:
            _emit("ingest-kindle", {"action": "error", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        _emit("ingest-kindle", result)
        verb = "captured" if result["applied"] else "dry-run: would capture"
        print(f"{verb} {result['new_highlights']} new highlight(s) across "
              f"{sum(1 for b in result['plan'] if b['new_highlights'])} book note(s); "
              f"{result['known_skipped']} already known.")
        for b in result["plan"]:
            mode = "append" if b["append"] else "create"
            print(f"  {mode}: {b['note']} (+{b['new_highlights']})")
        if not result["applied"]:
            print("Use --apply to write.")
        return 0

    if args.command == "ingest" and args.source == "readwise":
        token = os.environ.get("READWISE_TOKEN", "").strip()
        if not token:
            _emit("ingest-readwise", {"action": "error", "error": "READWISE_TOKEN not set", "ok": False})
            print("error: set READWISE_TOKEN in your environment (never in a file).", file=sys.stderr)
            return 1
        try:
            vault = Vault(args.vault)
            result = ingest_readwise(vault, token, since=args.since, apply=args.apply)
        except (ValueError, PermissionError, OSError) as e:
            _emit("ingest-readwise", {"action": "error", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        _emit("ingest-readwise", result)
        verb = "captured" if result["applied"] else "dry-run: would capture"
        print(f"{verb} {result['new_highlights']} new highlight(s) across "
              f"{len(result['plan'])} note(s) (since {result['since']}); "
              f"{result['known_skipped']} already known.")
        for b in result["plan"]:
            mode = "append" if b["append"] else "create"
            print(f"  {mode}: {b['note']} (+{b['new_highlights']})")
        if not result["applied"]:
            print("Use --apply to write.")
        return 0

    parser.error("unknown command")
    return 1


if __name__ == "__main__":
    sys.exit(main())
