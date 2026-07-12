"""`memex ingest rss` — pull one RSS/Atom feed into the vault. Feeds without a
cloud: your machine pulls, on your schedule (cron it yourself — there is no
daemon here by design).

Deterministic, stdlib-only parsing (RSS 2.0 + Atom). Incremental per feed via
`.memex/ingest_state.json`; volume-guarded (`--limit`, default 20) so a flooding
feed cannot bury `inbox/`. Item bodies are the summaries the feed itself
provides — full-page capture is `memex ingest url`'s job.
"""
from __future__ import annotations

import datetime
import email.utils
import hashlib
import html
import pathlib
import re
import urllib.request
import xml.etree.ElementTree as ET

import yaml

from .state import IngestState
from .vault import Vault

DEFAULT_LIMIT = 20
_TAGS = re.compile(r"<[^>]+>")
_WS = re.compile(r"\n{3,}")


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")
    return slug[:80].rstrip("-") or "item"


def _strip_html(text: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?</\1>", "", text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = _TAGS.sub("", text)
    return _WS.sub("\n\n", html.unescape(text)).strip()


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(el: ET.Element, name: str) -> str:
    for c in el:
        if _localname(c.tag) == name:
            return (c.text or "").strip()
    return ""


def _atom_link(el: ET.Element) -> str:
    fallback = ""
    for c in el:
        if _localname(c.tag) == "link":
            href = c.get("href", "")
            if c.get("rel", "alternate") == "alternate" and href:
                return href
            fallback = fallback or href
    return fallback


def _parse_date(raw: str) -> str:
    if not raw:
        return ""
    try:
        return email.utils.parsedate_to_datetime(raw).date().isoformat()
    except (TypeError, ValueError):
        pass
    try:
        return datetime.datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return raw[:10]


def parse_feed(data: bytes) -> dict:
    """RSS 2.0 or Atom → {title, items: [{id, title, link, date, summary}]} (feed order)."""
    root = ET.fromstring(data)
    rootname = _localname(root.tag)
    items = []
    if rootname == "rss":
        channel = next((c for c in root if _localname(c.tag) == "channel"), None)
        if channel is None:
            raise ValueError("malformed RSS: no <channel>")
        feed_title = _child_text(channel, "title")
        for it in channel:
            if _localname(it.tag) != "item":
                continue
            link = _child_text(it, "link")
            items.append({
                "id": _child_text(it, "guid") or link,
                "title": _child_text(it, "title") or link or "(untitled)",
                "link": link,
                "date": _parse_date(_child_text(it, "pubdate")),
                "summary": _strip_html(_child_text(it, "description")
                                       or _child_text(it, "encoded")),
            })
    elif rootname == "feed":
        feed_title = _child_text(root, "title")
        for it in root:
            if _localname(it.tag) != "entry":
                continue
            link = _atom_link(it)
            items.append({
                "id": _child_text(it, "id") or link,
                "title": _child_text(it, "title") or link or "(untitled)",
                "link": link,
                "date": _parse_date(_child_text(it, "published")
                                    or _child_text(it, "updated")),
                "summary": _strip_html(_child_text(it, "content")
                                       or _child_text(it, "summary")),
            })
    else:
        raise ValueError(f"not an RSS/Atom document (root <{rootname}>)")
    return {"title": feed_title or "(feed)", "items": items}


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "memex-cli"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def _item_key(item: dict) -> str:
    return hashlib.sha256((item["id"] or item["title"]).encode("utf-8")).hexdigest()[:16]


def _note_text(feed_url: str, feed_title: str, item: dict, now: datetime.datetime) -> str:
    frontmatter = {
        "title": item["title"],
        "status": "inbox",
        "captured_via": "rss",
        "captured_at": now.isoformat(),
        "feed_url": feed_url,
        "feed_title": feed_title,
    }
    if item["link"]:
        frontmatter["source_url"] = item["link"]
    if item["date"]:
        frontmatter["source_date"] = item["date"]
    body = item["summary"] or "(no summary in feed — capture the page with `memex ingest url`)"
    return (
        "---\n" + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)
        + "---\n\n" + body + "\n"
    )


def ingest_rss(
    vault: Vault, feed_url: str, apply: bool = False,
    limit: int = DEFAULT_LIMIT, since: str | None = None,
    data: bytes | None = None,
) -> dict:
    """`data` overrides the network fetch (tests/offline)."""
    if data is None:
        data = fetch_bytes(feed_url)
    feed = parse_feed(data)

    state = IngestState(vault.root)
    feeds = state.data.setdefault("rss", {})
    fkey = hashlib.sha256(feed_url.encode("utf-8")).hexdigest()[:24]
    rec = feeds.get(fkey, {"url": feed_url, "seen": []})

    fresh = [it for it in feed["items"] if _item_key(it) not in rec["seen"]]
    if since:
        fresh = [it for it in fresh if not it["date"] or it["date"] >= since[:10]]
    skipped_by_limit = max(0, len(fresh) - limit) if limit else 0
    fresh = fresh[:limit] if limit else fresh

    now = datetime.datetime.now(datetime.timezone.utc)
    target_dir = vault.write_target()
    plan = []
    for it in fresh:
        stamp = now.strftime("%Y%m%dT%H%M%SZ")
        base = f"{_slugify(it['title'])}-{stamp}"
        name = f"{base}.md"
        i = 1
        while (target_dir / name).exists() or any(p["note"].endswith("/" + name) for p in plan):
            name = f"{base}-{i}.md"
            i += 1
        rel = str(pathlib.Path(vault.write_dir()) / name)
        plan.append({"title": it["title"], "note": rel, "date": it["date"]})
        if not apply:
            continue
        full = vault.root / rel
        if full.resolve().parent != target_dir:
            raise PermissionError(f"write escapes boundary: {rel}")
        target_dir.mkdir(parents=True, exist_ok=True)
        full.write_text(_note_text(feed_url, feed["title"], it, now), encoding="utf-8")
        rec["seen"].append(_item_key(it))

    if apply and plan:
        feeds[fkey] = rec
        state.save()
    return {"action": "ingest-rss", "feed": feed_url, "feed_title": feed["title"],
            "items_in_feed": len(feed["items"]), "new_items": len(plan),
            "skipped_by_limit": skipped_by_limit, "plan": plan,
            "applied": apply, "ok": True}
