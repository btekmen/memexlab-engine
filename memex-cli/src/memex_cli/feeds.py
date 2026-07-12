"""YouTube channel feeds + the `feeds.md` subscriptions file.

`memex ingest youtube-feed <channel>` resolves a channel (UC-id, /channel/ URL,
@handle, or handle URL) to YouTube's official public RSS endpoint — the same
endpoint anyone can use, no API key — and pulls it through the rss machinery.
Video items are metadata notes; transcript capture is a separate concern.

`memex ingest feeds` iterates the vault's `feeds.md` — a human-editable markdown
list, one subscription per `- ` line, `#tag` tokens become default tags:

    - https://example.com/feed.xml #ai #research
    - @somechannel #video
    - UCxxxxxxxxxxxxxxxxxxxxxx

A failing feed never stops the others (per-source isolation).
"""
from __future__ import annotations

import re

from .ingest_rss import fetch_bytes, ingest_rss
from .vault import Vault

FEEDS_FILE = "feeds.md"
YT_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
_UC = re.compile(r"\b(UC[0-9A-Za-z_-]{22})\b")
_HANDLE = re.compile(r"@([\w.-]+)")


def resolve_channel(channel: str, fetch=fetch_bytes) -> str:
    """Channel input → official feed URL. Fetches the channel page only for handles."""
    channel = channel.strip()
    m = _UC.search(channel)
    if m:
        return YT_FEED.format(cid=m.group(1))
    m = _HANDLE.search(channel)
    if m:
        html_bytes = fetch(f"https://www.youtube.com/@{m.group(1)}")
        mm = _UC.search(html_bytes.decode("utf-8", errors="replace"))
        if mm:
            return YT_FEED.format(cid=mm.group(1))
        raise ValueError(f"could not resolve channel id for @{m.group(1)}")
    raise ValueError(f"unrecognized channel reference: {channel!r} "
                     "(use a UC… id, /channel/ URL, or @handle)")


def ingest_youtube_feed(vault: Vault, channel: str, apply: bool = False,
                        limit: int = 20, since: str | None = None,
                        data: bytes | None = None,
                        default_tags: list[str] | None = None) -> dict:
    feed_url = resolve_channel(channel)
    result = ingest_rss(vault, feed_url, apply=apply, limit=limit, since=since,
                        data=data, via="youtube-feed", default_tags=default_tags)
    result["channel"] = channel
    return result


def parse_feeds_file(text: str) -> list[dict]:
    """feeds.md → [{target, kind, tags}]; non-list lines and comments ignored."""
    subs = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        tokens = line[2:].split()
        if not tokens:
            continue
        target = tokens[0]
        tags = [t.lstrip("#") for t in tokens[1:] if t.startswith("#")]
        if target.startswith("@") or _UC.fullmatch(target) or "youtube.com" in target:
            kind = "youtube-feed"
        else:
            kind = "rss"
        subs.append({"target": target, "kind": kind, "tags": tags})
    return subs


def ingest_feeds(vault: Vault, apply: bool = False, limit: int = 20) -> dict:
    feeds_path = vault.root / FEEDS_FILE
    if not feeds_path.is_file():
        raise ValueError(f"no {FEEDS_FILE} in the vault — create it with one "
                         f"subscription per '- ' line")
    subs = parse_feeds_file(feeds_path.read_text(encoding="utf-8"))
    results = []
    total_new = 0
    for sub in subs:
        try:
            if sub["kind"] == "youtube-feed":
                r = ingest_youtube_feed(vault, sub["target"], apply=apply,
                                        limit=limit, default_tags=sub["tags"] or None)
            else:
                r = ingest_rss(vault, sub["target"], apply=apply, limit=limit,
                               default_tags=sub["tags"] or None)
            total_new += r["new_items"]
            results.append({"target": sub["target"], "kind": sub["kind"],
                            "ok": True, "new_items": r["new_items"],
                            "skipped_by_limit": r["skipped_by_limit"]})
        except Exception as e:  # per-source isolation: one bad feed never stops the rest
            results.append({"target": sub["target"], "kind": sub["kind"],
                            "ok": False, "error": str(e)})
    return {"action": "ingest-feeds", "subscriptions": len(subs),
            "new_items": total_new,
            "failures": sum(1 for r in results if not r["ok"]),
            "results": results, "applied": apply, "ok": True}
