"""Compact prompt index — one line per note, never the body.

The line shape is ``[[slug]] | title | section | type | status``. Empty type
and status are omitted from the line and returned as empty strings on the
structured rows. ``status`` and ``type`` are copied from frontmatter when a
note already has them. This module does not invent either field.

Notes with ``status: contested`` are listed first so a truncated index still
shows the conflict. A contested note also appends ``contests [[slug]]``. A
resolution proposal appends ``resolution: proposed``. Notes without those
fields keep the previous line.
"""
from __future__ import annotations

DEFAULT_LIMIT = 200
MAX_LIMIT = 500
DEFAULT_MAX_CHARS = 6000
TITLE_MAX = 80


def _clip(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3].rstrip() + "..."


def _scalar(value) -> str:
    if value is None or isinstance(value, (list, dict)):
        return ""
    return _clip(str(value), 40)


def _check_section(section) -> str | None:
    if section is None:
        return None
    if not isinstance(section, str):
        raise ValueError("section must be a single top-level folder name")
    name = section.strip().strip("/")
    if not name or "/" in name or "\\" in name or name in {".", ".."} or ".." in name:
        raise ValueError("section must be a single top-level folder name")
    return name


def _format_line(row: dict) -> str:
    parts = [f"[[{row['slug']}]]", row["title"] or row["slug"]]
    if row["section"]:
        parts.append(row["section"])
    if row["type"]:
        parts.append(row["type"])
    if row["status"]:
        parts.append(row["status"])
    if row.get("contests"):
        parts.append("contests " + " ".join(f"[[{s}]]" for s in row["contests"]))
    if row.get("resolution"):
        parts.append(f"resolution: {row['resolution']}")
    return " | ".join(parts)


def _contests(value) -> list[str]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        text = _scalar(item)
        if text:
            out.append(text)
    return out


def build_prompt_index(vault, limit: int = DEFAULT_LIMIT, section: str | None = None,
                       max_chars: int = DEFAULT_MAX_CHARS) -> dict:
    """Return a prompt string and the rows that went into it.

    ``truncated`` is true when ``limit`` or ``max_chars`` dropped notes.
    Bodies are never read into the prompt.
    """
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be an integer >= 1")
    if isinstance(max_chars, bool) or not isinstance(max_chars, int) or max_chars < 40:
        raise ValueError("max_chars must be an integer >= 40")
    limit = min(limit, MAX_LIMIT)
    section_filter = _check_section(section)
    rows = []
    for rel in vault.notes():
        folder = rel.parts[0] if len(rel.parts) > 1 else ""
        if section_filter is not None and folder != section_filter:
            continue
        try:
            note = vault.read(str(rel))
        except (ValueError, OSError, FileNotFoundError):
            continue
        fm = note["frontmatter"] if isinstance(note.get("frontmatter"), dict) else {}
        row = {
            "slug": rel.stem,
            "path": str(rel),
            "title": _clip(str(fm.get("title") or rel.stem), TITLE_MAX),
            "section": folder,
            "type": _scalar(fm.get("type")),
            "status": _scalar(fm.get("status")),
        }
        contests = _contests(fm.get("contests"))
        if contests:
            row["contests"] = contests
        resolution = _scalar(fm.get("resolution"))
        if resolution:
            row["resolution"] = resolution
        rows.append(row)
    rows.sort(key=lambda row: (0 if row["status"].casefold() == "contested" else 1, row["path"]))
    selected = []
    lines = []
    used = 0
    for row in rows:
        if len(selected) >= limit:
            break
        line = _format_line(row)
        addition = len(line) if not lines else len(line) + 1
        if lines and used + addition > max_chars:
            break
        if not lines and len(line) > max_chars:
            line = line[:max_chars]
            addition = len(line)
        selected.append(row)
        lines.append(line)
        used += addition
    return {
        "count": len(selected),
        "total": len(rows),
        "truncated": len(selected) < len(rows),
        "prompt": "\n".join(lines),
        "notes": selected,
    }
