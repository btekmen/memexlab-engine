#!/usr/bin/env python3
"""Ingest Kindle "My Clippings.txt" as one source note per book in raw/.

Deterministic, stdlib-only, no network. Dry-run by default; --apply writes.
Re-imports merge by (location, text-hash) and never duplicate; unrecognized
metadata lines fail loud, never guess (RFC-008, kindle half).
"""
import argparse
import datetime
import hashlib
import pathlib
import re
import sys

SEPARATOR = "=========="
_TITLE = re.compile(r"^(.*?)(?:\s*\(([^()]+)\))?\s*$")
_META = re.compile(
    r"^- Your (Highlight|Note|Bookmark)"
    r"(?: on page ([\w-]+))?"
    r"(?:(?: \|)? (?:at )?location ([\w-]+))?"
    r" \| Added on (.+)$"
)
_MARKER = re.compile(r"<!-- clip:([\w-]*):([0-9a-f]{8}) -->")


def _parse_date(raw: str) -> str:
    try:
        dt = datetime.datetime.strptime(raw.strip(), "%A, %B %d, %Y %I:%M:%S %p")
        return dt.date().isoformat()
    except ValueError:
        return raw.strip()  # keep verbatim rather than guess


def parse_clippings(path: pathlib.Path) -> list[dict]:
    text = pathlib.Path(path).read_text(encoding="utf-8-sig")
    clippings = []
    for entry in text.split(SEPARATOR):
        lines = [line.rstrip("\r") for line in entry.strip("\r\n").split("\n")]
        if not any(line.strip() for line in lines):
            continue
        if len(lines) < 2:
            sys.exit(f"error: unrecognized clippings entry: {lines[0]!r}")
        m_title = _TITLE.match(lines[0].lstrip("﻿"))
        m_meta = _META.match(lines[1].strip())
        if not m_meta:
            sys.exit(f"error: unrecognized metadata line: {lines[1]!r}")
        kind = m_meta.group(1).lower()
        if kind == "bookmark":
            continue
        body = "\n".join(lines[2:]).strip()
        clippings.append({
            "title": m_title.group(1).strip(),
            "author": (m_title.group(2) or "").strip(),
            "kind": kind,
            "page": m_meta.group(2) or "",
            "location": m_meta.group(3) or "",
            "date": _parse_date(m_meta.group(4)),
            "text": body,
        })
    return clippings


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "book"


def _identity(clip: dict) -> tuple:
    digest = hashlib.sha1(clip["text"].encode("utf-8")).hexdigest()[:8]
    return (clip["location"], digest)


def _render_clip(clip: dict) -> str:
    loc, digest = _identity(clip)
    attribution = []
    if clip["kind"] == "note":
        attribution.append("note")
    if clip["page"]:
        attribution.append(f"page {clip['page']}")
    if clip["location"]:
        attribution.append(f"location {clip['location']}")
    attribution.append(clip["date"])
    quoted = "\n".join(f"> {line}" for line in clip["text"].splitlines())
    return (f"<!-- clip:{loc}:{digest} -->\n{quoted}\n"
            f"— {' · '.join(attribution)}\n")


def _render_book(title: str, author: str, clips: list[dict]) -> str:
    front = ["---", "type: source", "source: kindle"]
    if author:
        front.append(f"author: {author}")
    front += ["---", "", f"# {title}", ""]
    return "\n".join(front) + "\n" + "\n".join(_render_clip(c) for c in clips)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clippings", help="path to My Clippings.txt")
    parser.add_argument("--vault", required=True, help="vault root")
    parser.add_argument("--apply", action="store_true",
                        help="write notes (default: dry-run preview)")
    args = parser.parse_args(argv)

    path = pathlib.Path(args.clippings)
    if not path.is_file():
        sys.exit(f"error: no such file: {path}")
    raw_dir = pathlib.Path(args.vault) / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    books: dict[tuple, list[dict]] = {}
    for clip in parse_clippings(path):
        books.setdefault((clip["title"], clip["author"]), []).append(clip)

    total_new = 0
    for (title, author), clips in books.items():
        target = raw_dir / f"kindle-{_slug(title)}.md"
        if target.exists():
            existing = set(map(tuple, _MARKER.findall(
                target.read_text(encoding="utf-8"))))
            fresh = [c for c in clips if _identity(c) not in existing]
            action = "merge into" if fresh else "skip (up to date)"
        else:
            fresh = clips
            action = "write"
        total_new += len(fresh)
        if not args.apply:
            print(f"dry-run: would {action} {target} (+{len(fresh)} clippings)")
        elif not fresh:
            print(f"skip (up to date): {target}")
        elif target.exists():
            with target.open("a", encoding="utf-8") as fh:
                fh.write("\n" + "\n".join(_render_clip(c) for c in fresh))
            print(f"merged {len(fresh)} clippings into {target}")
        else:
            target.write_text(_render_book(title, author, fresh),
                              encoding="utf-8")
            print(f"wrote {target} ({len(fresh)} clippings)")

    mode = "" if args.apply else "dry-run: "
    print(f"{mode}{total_new} new clippings across {len(books)} books")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
