"""`memex ingest kindle` — deterministic My Clippings.txt importer. No network,
no LLM. One note per book in the vault's write dir; re-imports append only new
highlights (identity = book + location + text hash) and never rewrite what's
already on disk, so your edits to the note survive.
"""
from __future__ import annotations

import datetime
import hashlib
import pathlib
import re

import yaml

from .state import IngestState
from .vault import Vault

SEPARATOR = re.compile(r"^=+\s*$")
META = re.compile(
    r"^-\s+Your\s+(?P<kind>Highlight|Note|Bookmark)"
    r"(?:\s+on\s+page\s+(?P<page>[\divxlc-]+))?"
    r".*?(?:Location\s+(?P<loc>[\d-]+))?"
    r"(?:\s*\|\s*Added\s+on\s+(?P<added>.+))?$",
    re.IGNORECASE,
)
TITLE_AUTHOR = re.compile(r"^(?P<title>.+?)\s*\((?P<author>[^()]+)\)\s*$")


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")
    return slug[:80].rstrip("-") or "book"


def _book_key(title: str, author: str) -> str:
    return hashlib.sha256(f"{title}\x00{author}".encode("utf-8")).hexdigest()[:24]


def _clip_hash(loc: str, page: str, text: str) -> str:
    return hashlib.sha256(f"{loc}\x00{page}\x00{text}".encode("utf-8")).hexdigest()[:16]


def parse_clippings(raw: str) -> list[dict]:
    """My Clippings.txt → [{title, author, kind, page, loc, added, text}] (bookmarks dropped)."""
    raw = raw.lstrip("﻿").replace("\r\n", "\n")
    entries = []
    block: list[str] = []
    for line in raw.split("\n") + ["=========="]:
        if SEPARATOR.match(line):
            lines = [l for l in block if l.strip() != ""]
            block = []
            if len(lines) < 2:
                continue
            tm = TITLE_AUTHOR.match(lines[0].strip())
            title = tm.group("title").strip() if tm else lines[0].strip()
            author = tm.group("author").strip() if tm else ""
            mm = META.match(lines[1].strip())
            kind = (mm.group("kind") if mm else "Highlight").capitalize()
            if kind == "Bookmark":
                continue
            text = "\n".join(l.rstrip() for l in lines[2:]).strip()
            if not text:
                continue
            entries.append({
                "title": title, "author": author, "kind": kind,
                "page": (mm.group("page") or "") if mm else "",
                "loc": (mm.group("loc") or "") if mm else "",
                "added": ((mm.group("added") or "").strip()) if mm else "",
                "text": text,
            })
        else:
            block.append(line)
    return entries


def _render_clip(e: dict) -> str:
    refs = [r for r in (
        f"page {e['page']}" if e["page"] else "",
        f"loc {e['loc']}" if e["loc"] else "",
        e["added"],
    ) if r]
    quoted = "\n".join("> " + l for l in e["text"].split("\n"))
    label = "" if e["kind"] == "Highlight" else f"**{e['kind']}.** "
    return f"{label}{quoted}\n— {' · '.join(refs) if refs else 'kindle'}\n"


def _new_book_note(title: str, author: str, now: datetime.datetime) -> str:
    frontmatter = {
        "title": title,
        "status": "inbox",
        "captured_via": "kindle",
        "captured_at": now.isoformat(),
    }
    if author:
        frontmatter["source_author"] = author
    return (
        "---\n" + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)
        + "---\n\n# " + title + "\n\n## Highlights\n"
    )


def ingest_kindle(vault: Vault, clippings_path: str, apply: bool = False) -> dict:
    raw = pathlib.Path(clippings_path).read_text(encoding="utf-8", errors="replace")
    entries = parse_clippings(raw)
    state = IngestState(vault.root)
    state.data.setdefault("kindle", {})

    now = datetime.datetime.now(datetime.timezone.utc)
    target_dir = vault.write_target()
    books: dict[str, dict] = {}
    new_count = known_count = 0

    for e in entries:
        key = _book_key(e["title"], e["author"])
        rec = state.data["kindle"].get(key, {"note": "", "hashes": []})
        book = books.setdefault(key, {
            "title": e["title"], "author": e["author"], "rec": rec,
            "new": [], "existing_note": rec.get("note", ""),
        })
        h = _clip_hash(e["loc"], e["page"], e["text"])
        if h in book["rec"]["hashes"] or h in [c[0] for c in book["new"]]:
            known_count += 1
            continue
        book["new"].append((h, e))
        new_count += 1

    plan = []
    for key, book in books.items():
        if not book["new"]:
            continue
        note_rel = book["existing_note"]
        exists = bool(note_rel) and (vault.root / note_rel).exists()
        if not exists:
            note_rel = str(pathlib.Path(vault.write_dir())
                           / f"{_slugify(book['title'])}-{now.strftime('%Y%m%dT%H%M%SZ')}.md")
        plan.append({"book": book["title"], "note": note_rel,
                     "new_highlights": len(book["new"]), "append": exists})
        if not apply:
            continue
        full = vault.root / note_rel
        if full.resolve().parent != target_dir and not exists:
            raise PermissionError(f"write escapes boundary: {note_rel}")
        if not exists:
            target_dir.mkdir(parents=True, exist_ok=True)
            full.write_text(_new_book_note(book["title"], book["author"], now),
                            encoding="utf-8")
        with full.open("a", encoding="utf-8") as f:
            for _, e in book["new"]:
                f.write("\n" + _render_clip(e))
        rec = state.data["kindle"].setdefault(key, {"note": note_rel, "hashes": []})
        rec["note"] = note_rel
        rec["hashes"].extend(h for h, _ in book["new"])

    if apply and new_count:
        state.save()
    return {"action": "ingest-kindle", "file": str(clippings_path),
            "books": len(books), "new_highlights": new_count,
            "known_skipped": known_count, "plan": plan, "applied": apply, "ok": True}
