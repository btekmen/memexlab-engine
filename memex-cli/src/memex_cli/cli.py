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
from . import index as index_mod, llm, views as views_mod
from .qa import qa as run_qa
from .ingest_url import ingest_url
from .search import search as search_vault
from .ingest_youtube import ingest_youtube
from .vault import Vault
from . import governance, queue as queue_mod


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
    search_p.add_argument("--mode", choices=["keyword", "hybrid"], default="keyword",
                          help="hybrid = BM25 + cached semantic index (run reindex first)")
    search_p.add_argument("--format", choices=["text", "json"], default="text")

    qa_p = sub.add_parser("qa", help="ask a question; get a [[slug]]-cited answer (needs a model)")
    qa_p.add_argument("question")
    qa_p.add_argument("--vault", default=os.environ.get("MEMEX_VAULT", "."),
                      help="vault root (or set MEMEX_VAULT; default: cwd)")
    qa_p.add_argument("--lens", default=None,
                      help="keypoints | eli5 | translate (with --lang) | counter | actions")
    qa_p.add_argument("--lang", default=None, help="target language for --lens translate")
    qa_p.add_argument("--view", default=None, help="restrict retrieval to a saved view")
    qa_p.add_argument("--include", action="append", default=[],
                      help="force-pin a note slug into context (repeatable)")
    qa_p.add_argument("--limit", type=int, default=6, help="retrieved notes (default 6)")
    qa_p.add_argument("--max-tokens", type=int, default=1000)
    qa_p.add_argument("--apply", action="store_true",
                      help="also file the answer into the qa dir (default: stdout only)")
    qa_p.add_argument("--strict", action="store_true",
                      help="exit 1 on missing/invalid citations")
    qa_p.add_argument("--format", choices=["text", "json"], default="text")
    ytv_p = ingest_sub.add_parser("youtube", help="capture a video's transcript with timestamp anchors")
    ytv_p.add_argument("url", help="video URL (watch, youtu.be, shorts)")
    ytv_p.add_argument("--vault", default=os.environ.get("MEMEX_VAULT", "."),
                       help="vault root (or set MEMEX_VAULT; default: cwd)")
    ytv_p.add_argument("--lang", default=None, help="caption language code (default: uploaded track, else first)")
    ytv_p.add_argument("--apply", action="store_true", help="write the note (default: dry-run)")
    ytv_p.add_argument("--force", action="store_true", help="re-capture an already-ingested video")

    re_p = sub.add_parser("reindex", help="build/refresh the local semantic index (a rebuildable cache)")
    re_p.add_argument("--vault", default=os.environ.get("MEMEX_VAULT", "."),
                      help="vault root (or set MEMEX_VAULT; default: cwd)")
    re_p.add_argument("--apply", action="store_true",
                      help="embed changed/new notes (default: dry-run staleness plan)")
    re_p.add_argument("--verify", action="store_true",
                      help="exit 1 unless the index is current (CI/reproducibility check)")

    save_p = sub.add_parser("save", help="capture a note into inbox/ with provenance")
    save_p.add_argument("title", help="note title")
    save_p.add_argument("body", nargs="?", default="",
                        help="note body (stdin if omitted)")
    save_p.add_argument("--vault", default=os.environ.get("MEMEX_VAULT", "."),
                        help="vault root (or set MEMEX_VAULT; default: cwd)")
    save_p.add_argument("--sources", action="append", default=[],
                        help="source note slugs (repeatable)")
    save_p.add_argument("--apply", action="store_true",
                        help="write the note (default: dry-run preview)")

    ask_p = sub.add_parser("ask", help="search + answer with [[slug]] citations")
    ask_p.add_argument("question")
    ask_p.add_argument("--vault", default=os.environ.get("MEMEX_VAULT", "."),
                        help="vault root (or set MEMEX_VAULT; default: cwd)")
    ask_p.add_argument("--view", default=None, help="restrict to a saved view")
    ask_p.add_argument("--limit", type=int, default=6, help="retrieved notes (default 6)")
    ask_p.add_argument("--format", choices=["text", "json"], default="text")

    approve_p = sub.add_parser("approve", help="list/complete/drop queue items")
    approve_p.add_argument("item", nargs="?", default=None,
                           help="queue item slug (omit to list pending)")
    approve_p.add_argument("--vault", default=os.environ.get("MEMEX_VAULT", "."),
                           help="vault root (or set MEMEX_VAULT; default: cwd)")
    approve_p.add_argument("--yes", action="store_true",
                           help="complete the item (needs --result-title and --result-body)")
    approve_p.add_argument("--no", action="store_true",
                           help="drop the item (cancel without result)")
    approve_p.add_argument("--result-title", default=None,
                           help="title for the result note (required with --yes)")
    approve_p.add_argument("--result-body", default=None,
                           help="body for the result note (stdin if omitted with --yes)")
    approve_p.add_argument("--apply", action="store_true",
                           help="write changes (default: dry-run)")
    approve_p.add_argument("--format", choices=["text", "json"], default="text")

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
            if args.mode == "hybrid":
                wide = search_vault(vault, args.query, limit=max(args.limit * 4, 20),
                                    allowed=allowed)
                hits = index_mod.hybrid_rank(vault, args.query, wide, args.limit,
                                             allowed=allowed)
        except (RuntimeError, ValueError, PermissionError, OSError) as e:
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

    if args.command == "qa":
        try:
            vault = Vault(args.vault)
            result = run_qa(vault, args.question, lens=args.lens, lang=args.lang,
                            view=args.view, include=args.include, k=args.limit,
                            max_tokens=args.max_tokens, apply=args.apply,
                            strict=args.strict)
        except RuntimeError as e:
            _emit("qa", {"action": "refused", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        except (ValueError, PermissionError, OSError) as e:
            _emit("qa", {"action": "error", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        _emit("qa", {k_: v for k_, v in result.items() if k_ != "answer"})
        if result["action"] == "no-context":
            print(f"error: {result['hint']}", file=sys.stderr)
            return 1
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result["answer"].strip())
            note = f" · filed: {result['note']}" if result.get("note") else ""
            print(f"\n[{result['citations_valid']}/{result['citations_total']} citations valid"
                  f" · {result['route']}:{result['model']}{note}]", file=sys.stderr)
        return 0 if result["ok"] else 1
    if args.command == "ingest" and args.source == "youtube":
        try:
            vault = Vault(args.vault)
            result = ingest_youtube(vault, args.url, apply=args.apply,
                                    force=args.force, lang=args.lang)
        except (ValueError, PermissionError, OSError) as e:
            _emit("ingest-youtube", {"action": "error", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        _emit("ingest-youtube", result)
        if not result["ok"]:
            hint = f" — {result['hint']}" if result.get("hint") else ""
            print(f"error: {result['action']} for {args.url}{hint}")
            return 1
        if result["action"] == "skip-duplicate":
            print(f"already captured: {result['note']} (use --force to re-capture)")
        elif result["applied"]:
            print(f"captured: {result['note']} ({result['anchors']} anchors, "
                  f"{result['transcript_kind']} captions)")
        else:
            print(f"dry-run: would write {result['note']} — {result['segments']} caption "
                  f"segments into {result['anchors']} timestamp anchors "
                  f"({result['transcript_kind']}). Use --apply to write.")
        return 0

    if args.command == "reindex":
        try:
            vault = Vault(args.vault)
            if args.verify:
                status = index_mod.index_status(vault)
                _emit("reindex", {"action": "verify", **status, "ok": status["current"]})
                print("index is current" if status["current"] else
                      f"index is STALE ({status['stale']} stale, {status['missing']} missing)")
                return 0 if status["current"] else 1
            result = index_mod.reindex(vault, apply=args.apply)
        except RuntimeError as e:
            _emit("reindex", {"action": "refused", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        except (ValueError, PermissionError, OSError) as e:
            _emit("reindex", {"action": "error", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        _emit("reindex", result)
        if result["applied"]:
            print(f"embedded {result.get('embedded', 0)} note(s) with "
                  f"{result.get('model', '?')}; index current: {result['current']}")
        else:
            print(f"dry-run: {result['to_embed']} note(s) need embedding "
                  f"({result['fresh']} fresh, {result['stale']} stale, "
                  f"{result['missing']} missing). Use --apply to embed.")
        return 0

    if args.command == "save":
        body = args.body
        if not body:
            if not sys.stdin.isatty():
                body = sys.stdin.read()
            else:
                body = ""
        if not body.strip():
            _emit("save", {"action": "error", "error": "body is required (pass as arg or stdin)", "ok": False})
            print("error: body is required (pass as arg or via stdin)", file=sys.stderr)
            return 1
        try:
            vault = Vault(args.vault)
            if args.apply:
                result = governance.capture_note(vault, args.title, body, sources=args.sources or None)
                result["action"] = "save"
                result["applied"] = True
                result["ok"] = True
            else:
                wd = governance.write_dir(vault.root)
                slug = governance._slugify(args.title)
                result = {"action": "save", "applied": False, "ok": True,
                          "title": args.title, "slug": slug, "write_dir": wd,
                          "chars": len(body), "sources": args.sources}
        except (ValueError, PermissionError, OSError) as e:
            _emit("save", {"action": "error", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        _emit("save", result)
        if result["applied"]:
            print(f"saved: {result['path']}")
        else:
            print(f"dry-run: would write {result['slug']} to {result['write_dir']}/ "
                  f"({result['chars']} chars). Use --apply to write.")
        return 0

    if args.command == "ask":
        try:
            vault = Vault(args.vault)
            result = run_qa(vault, args.question, view=args.view, k=args.limit,
                            max_tokens=1000, apply=False, strict=False)
        except RuntimeError as e:
            _emit("ask", {"action": "refused", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        except (ValueError, PermissionError, OSError) as e:
            _emit("ask", {"action": "error", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        _emit("ask", {k_: v for k_, v in result.items() if k_ != "answer"})
        if result["action"] == "no-context":
            print(f"error: {result['hint']}", file=sys.stderr)
            return 1
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result["answer"].strip())
            print(f"\n[{result['citations_valid']}/{result['citations_total']} citations valid "
                  f"· {result['route']}:{result['model']}]", file=sys.stderr)
        return 0 if result["ok"] else 1

    if args.command == "approve":
        try:
            vault = Vault(args.vault)
            if args.item is None:
                items = queue_mod.list_queue(vault, status="pending")
                result = {"action": "list-queue", "items": items, "count": len(items), "ok": True}
                _emit("approve", result)
                if args.format == "json":
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                else:
                    if not items:
                        print("no pending queue items")
                    for it in items:
                        print(f"{it['item']}\t{it['title']}\t[{it['status']}]")
                return 0
            
            if args.yes and args.no:
                _emit("approve", {"action": "error", "error": "cannot use --yes and --no together", "ok": False})
                print("error: cannot use --yes and --no together", file=sys.stderr)
                return 1
            
            if args.yes:
                if not args.result_title:
                    _emit("approve", {"action": "error", "error": "--yes needs --result-title", "ok": False})
                    print("error: --yes needs --result-title", file=sys.stderr)
                    return 1
                result_body = args.result_body
                if not result_body:
                    if not sys.stdin.isatty():
                        result_body = sys.stdin.read()
                    else:
                        result_body = ""
                if not result_body.strip():
                    _emit("approve", {"action": "error", "error": "result body required (--result-body or stdin)", "ok": False})
                    print("error: result body required (--result-body or via stdin)", file=sys.stderr)
                    return 1
                
                if args.apply:
                    result = queue_mod.complete_queue_item(vault, args.item, args.result_title, result_body)
                    result["action"] = "complete"
                    result["applied"] = True
                    result["ok"] = True
                else:
                    result = {"action": "complete", "applied": False, "ok": True,
                              "item": args.item, "result_title": args.result_title,
                              "result_chars": len(result_body)}
            elif args.no:
                if args.apply:
                    result = queue_mod.drop_queue_item(vault, args.item)
                    result["action"] = "drop"
                    result["applied"] = True
                    result["ok"] = True
                else:
                    result = {"action": "drop", "applied": False, "ok": True, "item": args.item}
            else:
                items = queue_mod.list_queue(vault, status="all")
                matching = [it for it in items if it["item"] == args.item]
                if not matching:
                    _emit("approve", {"action": "error", "error": f"no queue item named '{args.item}'", "ok": False})
                    print(f"error: no queue item named '{args.item}'", file=sys.stderr)
                    return 1
                result = {"action": "show-item", "item": matching[0], "ok": True}
                _emit("approve", result)
                if args.format == "json":
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                else:
                    it = matching[0]
                    print(f"item: {it['item']}")
                    print(f"title: {it['title']}")
                    print(f"status: {it['status']}")
                    print(f"path: {it['path']}")
                    print(f"\n{it['task']}")
                return 0
        except (ValueError, PermissionError, OSError) as e:
            _emit("approve", {"action": "error", "error": str(e), "ok": False})
            print(f"error: {e}", file=sys.stderr)
            return 1
        _emit("approve", result)
        if result["applied"]:
            if result["action"] == "complete":
                print(f"completed: {result['item']} → {result['result']}")
            elif result["action"] == "drop":
                print(f"cancelled: {result['item']}")
        else:
            if result["action"] == "complete":
                print(f"dry-run: would complete {result['item']} and file result note "
                      f"({result['result_chars']} chars). Use --apply to write.")
            elif result["action"] == "drop":
                print(f"dry-run: would cancel {result['item']}. Use --apply to write.")
        return 0

    parser.error("unknown command")
    return 1


if __name__ == "__main__":
    sys.exit(main())
