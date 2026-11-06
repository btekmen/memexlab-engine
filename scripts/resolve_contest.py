#!/usr/bin/env python3
"""File a contested note or a resolution proposal. Never edits an existing note.

This is not a migration. It does not add status to notes that lack one, and it
does not rewrite a note a conflict is about. Dry-run is the default: the
command prints the note it would file. ``--apply`` writes that new note into
the vault's inbox and needs the operator to run it. A human applies a
proposal by editing the vault themselves.

Usage:
  python3 scripts/resolve_contest.py capture --vault ~/vault \\
      --title "Launch moved" --body "The review is now July 2026." \\
      --contests sample-launch
  python3 scripts/resolve_contest.py propose --vault ~/vault \\
      --contest launch-moved-20261106T000000Z --proposal "Keep July 2026." --apply
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "memexlab-mcp" / "src"
if SRC.is_dir() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from memexlab_mcp.governance import capture_note, propose_resolution  # noqa: E402
from memexlab_mcp.vault import Vault  # noqa: E402


def _preview(kind: str, args) -> dict:
    return {
        "cmd": "resolve_contest",
        "action": kind,
        "applied": False,
        "vault": str(Path(args.vault).expanduser()),
        "would_write": "a new inbox note",
        "edits_existing_notes": False,
        "ok": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--vault", required=True, help="markdown vault")
    parser.add_argument("--apply", action="store_true",
                        help="write the new inbox note (default: print the plan only)")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    sub = parser.add_subparsers(dest="command", required=True)

    cap = sub.add_parser("capture", help="file a new contested (or lifecycle) note")
    cap.add_argument("--title", required=True)
    cap.add_argument("--body", required=True, help="the conflicting evidence")
    cap.add_argument("--contests", action="append", default=[],
                     help="slug the new evidence disagrees with (repeatable)")
    cap.add_argument("--status", default=None,
                     help="active, contested, stale, or archived; omit for the capture default")
    cap.add_argument("--origin-ref", default=None)
    cap.add_argument("--sources", action="append", default=[])

    prop = sub.add_parser("propose", help="file a resolution proposal for a human to approve")
    prop.add_argument("--contest", required=True, help="slug of the contested note")
    prop.add_argument("--proposal", required=True)
    prop.add_argument("--origin-ref", default=None)
    prop.add_argument("--sources", action="append", default=[])

    args = parser.parse_args(argv)
    try:
        vault = Vault(Path(args.vault).expanduser())
        if not args.apply:
            preview = _preview(args.command, args)
            if args.command == "capture":
                preview["title"] = args.title
                preview["contests"] = args.contests
                preview["status"] = args.status or ("contested" if args.contests else None)
            else:
                preview["contest"] = args.contest
            _emit(preview, args.format)
            return 0
        if args.command == "capture":
            result = capture_note(
                vault, args.title, args.body, sources=args.sources or None,
                agent="resolve_contest", origin_ref=args.origin_ref,
                status=args.status, contests=args.contests or None,
            )
        else:
            result = propose_resolution(
                vault, args.contest, args.proposal, sources=args.sources or None,
                agent="resolve_contest", origin_ref=args.origin_ref,
            )
    except (ValueError, FileNotFoundError, PermissionError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(json.dumps({"cmd": "resolve_contest", "ok": False, "error": str(exc)}),
              file=sys.stderr)
        return 1
    payload = {"cmd": "resolve_contest", "action": args.command, "applied": True,
               "edits_existing_notes": False, "ok": True, **result}
    payload.pop("note", None)
    _emit(payload, args.format)
    return 0


def _emit(payload: dict, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if payload.get("applied"):
        print(f"filed {payload.get('path')} status={payload.get('status')} "
              f"created={payload.get('created')}")
    else:
        print("dry-run: no note written. Pass --apply to file a new inbox note.")
        print("Existing notes are not edited.")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
