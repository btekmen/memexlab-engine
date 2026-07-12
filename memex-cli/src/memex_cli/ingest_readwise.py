"""`memex ingest readwise` — incremental import from the Readwise export API.

Token discipline: read from the READWISE_TOKEN environment variable only — never
from any file under version control (engine non-negotiable). The vault stays the
hub: Readwise is an upstream source we import FROM.

Highlight identity is Readwise's own highlight id, so re-imports are exact and
append-only: your edits to a book note survive. The incremental cursor lives in
`.memex/ingest_state.json` (rebuildable cache, never truth).
"""
from __future__ import annotations

import datetime
import json
import pathlib
import re
import urllib.parse
import urllib.request

import yaml

from .state import IngestState
from .vault import Vault

API = "https://readwise.io/api/v2/export/"


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")
    return slug[:80].rstrip("-") or "source"


def fetch_page(token: str, updated_after: str | None, cursor: str | None) -> dict:
    params = {}
    if updated_after:
        params["updatedAfter"] = updated_after
    if cursor:
        params["pageCursor"] = cursor
    url = API + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"Authorization": f"Token {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_export(token: str, updated_after: str | None) -> list[dict]:
    books: list[dict] = []
    cursor = None
    while True:
        page = fetch_page(token, updated_after, cursor)
        books.extend(page.get("results", []))
        cursor = page.get("nextPageCursor")
        if not cursor:
            return books


def _new_note(book: dict, now: datetime.datetime) -> str:
    frontmatter = {
        "title": book.get("title") or "Untitled",
        "status": "inbox",
        "captured_via": "readwise",
        "captured_at": now.isoformat(),
    }
    if book.get("author"):
        frontmatter["source_author"] = book["author"]
    if book.get("source_url"):
        frontmatter["source_url"] = book["source_url"]
    if book.get("category"):
        frontmatter["source_category"] = book["category"]
    if book.get("user_book_id") is not None:
        frontmatter["readwise_id"] = book["user_book_id"]
    return (
        "---\n" + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)
        + "---\n\n# " + frontmatter["title"] + "\n\n## Highlights\n"
    )


def _render(h: dict) -> str:
    refs = [r for r in (
        f"loc {h['location']}" if h.get("location") else "",
        (h.get("highlighted_at") or "")[:10],
    ) if r]
    quoted = "\n".join("> " + l for l in (h.get("text") or "").split("\n"))
    out = f"{quoted}\n— {' · '.join(refs) if refs else 'readwise'}\n"
    if h.get("note"):
        out += f"**Note.** {h['note']}\n"
    return out


def ingest_readwise(
    vault: Vault, token: str, since: str | None = None, apply: bool = False,
    books: list[dict] | None = None,
) -> dict:
    """`books` overrides the API fetch (tests). `since` overrides the stored cursor."""
    state = IngestState(vault.root)
    rw = state.data.setdefault("readwise", {"cursor": None, "books": {}})
    updated_after = since or rw.get("cursor")

    if books is None:
        books = fetch_export(token, updated_after)

    now = datetime.datetime.now(datetime.timezone.utc)
    target_dir = vault.write_target()
    new_count = known_count = 0
    plan = []

    for book in books:
        key = str(book.get("user_book_id") or _slugify(book.get("title") or ""))
        rec = rw["books"].get(key, {"note": "", "ids": []})
        fresh = [h for h in book.get("highlights", [])
                 if str(h.get("id")) not in rec["ids"] and (h.get("text") or "").strip()]
        known = len(book.get("highlights", [])) - len(fresh)
        known_count += known
        if not fresh:
            continue
        new_count += len(fresh)
        note_rel = rec.get("note", "")
        exists = bool(note_rel) and (vault.root / note_rel).exists()
        if not exists:
            note_rel = str(pathlib.Path(vault.write_dir())
                           / f"{_slugify(book.get('title') or 'source')}-{now.strftime('%Y%m%dT%H%M%SZ')}.md")
        plan.append({"book": book.get("title") or "Untitled", "note": note_rel,
                     "new_highlights": len(fresh), "append": exists})
        if not apply:
            continue
        full = vault.root / note_rel
        if full.resolve().parent != target_dir and not exists:
            raise PermissionError(f"write escapes boundary: {note_rel}")
        if not exists:
            target_dir.mkdir(parents=True, exist_ok=True)
            full.write_text(_new_note(book, now), encoding="utf-8")
        with full.open("a", encoding="utf-8") as f:
            for h in fresh:
                f.write("\n" + _render(h))
        rec = rw["books"].setdefault(key, {"note": note_rel, "ids": []})
        rec["note"] = note_rel
        rec["ids"].extend(str(h["id"]) for h in fresh)

    if apply:
        rw["cursor"] = now.isoformat()
        state.save()
    return {"action": "ingest-readwise", "since": updated_after or "(full export)",
            "books_seen": len(books), "new_highlights": new_count,
            "known_skipped": known_count, "plan": plan, "applied": apply, "ok": True}
