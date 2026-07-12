"""`memex ingest url` — fetch a public page, extract readable markdown, file it
into the vault's write dir (default inbox/) with provenance. Dry-run by default.

Deterministic: no LLM anywhere in the capture path (invariant 4). Extraction is
local via trafilatura; what a local fetch cannot see (heavy JS, paywalls) is not
captured — we do not proxy through a cloud renderer.
"""
from __future__ import annotations

import datetime
import itertools
import pathlib
import re

import yaml

from .state import IngestState
from .vault import Vault


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")
    return slug[:80].rstrip("-") or "capture"


def fetch_html(url: str) -> str | None:
    import trafilatura

    return trafilatura.fetch_url(url)


def extract(html: str, url: str) -> dict:
    """Readable markdown + metadata from raw HTML. Returns {title, author, date, body}."""
    import trafilatura

    body = None
    try:
        body = trafilatura.extract(
            html, url=url, output_format="markdown", include_links=True,
            include_formatting=True, favor_recall=True,
        )
    except (TypeError, ValueError):
        pass
    if not body:
        body = trafilatura.extract(html, url=url, favor_recall=True)
    meta = {}
    try:
        m = trafilatura.extract_metadata(html, default_url=url)
        if m is not None:
            meta = m.as_dict()
    except Exception:
        meta = {}
    return {
        "title": (meta.get("title") or "").strip() or url,
        "author": (meta.get("author") or "").strip(),
        "date": (meta.get("date") or "").strip(),
        "body": (body or "").strip(),
    }


def build_note(url: str, page: dict, now: datetime.datetime) -> str:
    frontmatter = {
        "title": page["title"],
        "status": "inbox",
        "captured_via": "cli",
        "captured_at": now.isoformat(),
        "source_url": url,
    }
    if page["author"]:
        frontmatter["source_author"] = page["author"]
    if page["date"]:
        frontmatter["source_date"] = page["date"]
    return (
        "---\n" + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)
        + "---\n\n" + page["body"] + "\n"
    )


def ingest_url(
    vault: Vault, url: str, apply: bool = False, force: bool = False,
    html: str | None = None,
) -> dict:
    """Returns a result dict; the caller emits the JSON event.

    `html` overrides the network fetch (tests, offline files).
    """
    state = IngestState(vault.root)
    prior = state.seen_url(url)
    if prior and not force and (vault.root / prior["note"]).exists():
        return {"action": "skip-duplicate", "url": url, "note": prior["note"],
                "applied": False, "ok": True}

    if html is None:
        html = fetch_html(url)
    if not html:
        return {"action": "fetch-failed", "url": url, "applied": False, "ok": False}
    page = extract(html, url)
    if not page["body"]:
        return {"action": "extract-failed", "url": url, "applied": False, "ok": False}

    now = datetime.datetime.now(datetime.timezone.utc)
    note_text = build_note(url, page, now)
    target_dir = vault.write_target()
    slug = _slugify(page["title"])
    stamp = now.strftime("%Y%m%dT%H%M%SZ")

    rel: pathlib.Path | None = None
    for i in itertools.count():
        name = f"{slug}-{stamp}.md" if i == 0 else f"{slug}-{stamp}-{i}.md"
        cand = target_dir / name
        if cand.resolve().parent != target_dir:
            raise PermissionError(f"write escapes boundary: {name}")
        if not cand.exists():
            rel = cand.relative_to(vault.root)
            break

    result = {"action": "ingest-url", "url": url, "title": page["title"],
              "note": str(rel), "chars": len(page["body"]), "applied": apply, "ok": True}
    if not apply:
        return result

    target_dir.mkdir(parents=True, exist_ok=True)
    (vault.root / rel).write_text(note_text, encoding="utf-8")
    state.record_url(url, str(rel), now.isoformat())
    state.save()
    return result
