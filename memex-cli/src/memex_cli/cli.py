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
from .feeds import ingest_feeds, ingest_youtube_feed
from .ingest_rss import ingest_rss
from . import views as views_mod
from .ingest_url import ingest_url
from .search import search as search_vault
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

    rss_p = ingest_sub.add_parser("rss", help="pull one RSS/Atom feed into the write dir")
    rss_p.add_argument("feed_url", help="the feed URL")
    rss_p.add_argument("--vault", default=os.environ.get("MEMEX_VAULT", "."),
                       help="vault root (or set MEMEX_VAULT; default: cwd)")
    rss_p.add_argument("--limit", type=int, default=20,
                       help="max new items per run (volume guard; default 20)")
    rss_p.add_argument("--since", default=None,
                       help="only items dated on/after this ISO date")
    rss_p.add_argument("--apply", action="store_true",
                       help="write notes (default: dry-run preview)")

    yt_p = ingest_sub.add_parser("youtube-feed", help="pull a YouTube channel's public feed")
    yt_p.add_argument("channel", help="UC… id, /channel/ URL, or @handle")
    yt_p.add_argument("--vault", default=os.environ.get("MEMEX_VAULT", "."),
                      help="vault root (or set MEMEX_VAULT; default: cwd)")
    yt_p.add_argument("--limit", type=int, default=20, help="max new items per run (default 20)")
    yt_p.add_argument("--since", default=None, help="only items dated on/after this ISO date")
    yt_p.add_argument("--apply", action="store_true", help="write notes (default: dry-run)")

    feeds_p = ingest_sub.add_parser("feeds", help="pull every subscription in the vault's feeds.md")
    feeds_p.add_argument("--vault", default=os.environ.get("MEMEX_VAULT", "."),
                         help="vault root (or set MEMEX_VAULT; default: cwd)")
    feeds_p.add_argument("--limit", type=int, default=20, help="max new items per feed (default 20)")
    feeds_p.add_argument("--apply", action="store_true", help="write notes (default: dry-run)")

    view_p = sub.add_parser("view", help="list views, or a view's members (read-only)")
    view_p.add_argument("name", nargs="?", default=None,
                        help="view name from views/ (omit to list available views)")
    view_p.add_argument("--vault", default=os.environ.get("MEMEX_VAULT", "."),
                        help="vault root (or set MEMEX_VAULT; default: cwd)")
    view_p.add_argument("--format", choices=["text", "json"], default="text")

    search_p = sub.add_parser("search", help="deterministic BM25 search (read-only)")
    search_p.add_argument("query", help="search terms")
    search_p.add_argument("--vault", default=os.environ.get("MEMEX_VAULT", "."),
                          help="vault root (or set MEMEX_VAULT; default: cwd)")
    search_p.add_argument("--limit", type=int, default=5)
    search_p.add_argument("--view", default=None, help="restrict to a saved view's members")
    search_p.add_argument("--format", choices=["text", "json"], default="text")

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

    if args.command == "ingest" and args.source == "rss":
        try:
            vault = Vault(args.vault)
            result = ingest_rss(vault, args.feed_url, apply=args.apply,
                                limit=args.limit, since=args.since)
        except (ValueError, PermissionError, OSError) as e:
            _emit("ingest-rss", {"action": "error", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        _emit("ingest-rss", result)
        verb = "captured" if result["applied"] else "dry-run: would capture"
        guard = f" ({result['skipped_by_limit']} held back by --limit)" if result["skipped_by_limit"] else ""
        print(f"{verb} {result['new_items']} new item(s) from \"{result['feed_title']}\"{guard}.")
        for it in result["plan"]:
            print(f"  {it['note']}  [{it['date'] or 'undated'}]")
        if not result["applied"]:
            print("Use --apply to write.")
        return 0

    if args.command == "ingest" and args.source == "youtube-feed":
        try:
            vault = Vault(args.vault)
            result = ingest_youtube_feed(vault, args.channel, apply=args.apply,
                                         limit=args.limit, since=args.since)
        except (ValueError, PermissionError, OSError) as e:
            _emit("ingest-youtube-feed", {"action": "error", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        _emit("ingest-youtube-feed", result)
        verb = "captured" if result["applied"] else "dry-run: would capture"
        print(f"{verb} {result['new_items']} new video note(s) from \"{result['feed_title']}\".")
        for it in result["plan"]:
            print(f"  {it['note']}  [{it['date'] or 'undated'}]")
        if not result["applied"]:
            print("Use --apply to write.")
        return 0

    if args.command == "ingest" and args.source == "feeds":
        try:
            vault = Vault(args.vault)
            result = ingest_feeds(vault, apply=args.apply, limit=args.limit)
        except (ValueError, PermissionError, OSError) as e:
            _emit("ingest-feeds", {"action": "error", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        _emit("ingest-feeds", result)
        verb = "captured" if result["applied"] else "dry-run: would capture"
        print(f"{verb} {result['new_items']} new item(s) across {result['subscriptions']} "
              f"subscription(s); {result['failures']} failed.")
        for r in result["results"]:
            status = f"+{r['new_items']}" if r["ok"] else f"FAILED: {r['error']}"
            print(f"  {r['kind']}: {r['target']}  {status}")
        if not result["applied"]:
            print("Use --apply to write.")
        return 0 if result["failures"] < max(1, result["subscriptions"]) else 1

    if args.command == "view":
        try:
            vault = Vault(args.vault)
            if args.name is None:
                listing = views_mod.list_views(vault)
                result = {"action": "list-views", "views": listing, "ok": True}
            else:
                members = [str(m) for m in views_mod.members(vault, args.name)]
                result = {"action": "view-members", "view": args.name,
                          "members": members, "count": len(members), "ok": True}
        except (ValueError, PermissionError) as e:
            _emit("view", {"action": "error", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        _emit("view", result)
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.name is None:
            if not result["views"]:
                print("no views yet — create views/<name>.md with 'type: view' and a query: block")
            for v in result["views"]:
                print(f"{v['name']}\t{v['title']}")
        else:
            for m in result["members"]:
                print(m)
            print(f"({result['count']} note(s) in view '{args.name}')", file=sys.stderr)
        return 0

    if args.command == "search":
        try:
            vault = Vault(args.vault)
            allowed = None
            if args.view:
                allowed = {str(m) for m in views_mod.members(vault, args.view)}
            hits = search_vault(vault, args.query, limit=args.limit, allowed=allowed)
        except (ValueError, PermissionError) as e:
            _emit("search", {"action": "error", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        _emit("search", {"action": "search", "query": args.query,
                         "view": args.view, "hits": len(hits), "ok": True})
        if args.format == "json":
            print(json.dumps(hits, ensure_ascii=False, indent=2))
        else:
            for h in hits:
                print(f"[[{h['slug']}]]\t{h['path']}\t{h['snippet'][:70]}")
            if not hits:
                print("no hits")
        return 0

    parser.error("unknown command")
    return 1


if __name__ == "__main__":
    sys.exit(main())
