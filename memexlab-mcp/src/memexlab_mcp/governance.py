"""The write boundary. Agents may add to the write dir; they can never touch canonical."""
from __future__ import annotations

import datetime
import itertools
import json
import pathlib
import re

import yaml

from .vault import Vault, parse_frontmatter

DEFAULT_WRITE_DIR = "inbox"
LOG_REL = pathlib.Path(".memexlab") / "log.jsonl"
ORIGIN_REF_MAX = 256
# Optional lifecycle values. Notes that omit status, or that already use
# another value (inbox, draft, a queue status), stay valid.
LIFECYCLE_STATUSES = ("active", "contested", "stale", "archived")


class _QuotedStr(str):
    """A string PyYAML must emit quoted, so it cannot come back as a bool, date, or int."""


def _represent_quoted(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style='"')


yaml.SafeDumper.add_representer(_QuotedStr, _represent_quoted)


def write_dir(vault_root: pathlib.Path) -> str:
    gov = pathlib.Path(vault_root) / "governance.yml"
    if gov.is_file():
        try:
            data = yaml.safe_load(gov.read_text(encoding="utf-8")) or {}
            if isinstance(data, dict):
                wd = data.get("write_dir")
                if isinstance(wd, str) and wd.strip():
                    return wd.strip()
        except yaml.YAMLError:
            pass
    return DEFAULT_WRITE_DIR


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")
    slug = slug[:80].rstrip("-")
    return slug or "note"


def _normalize_origin_ref(origin_ref: str | None) -> str | None:
    """Return a stripped origin_ref, or None when the caller did not set one.

    Whitespace-only is treated as absent so a client that always sends the
    field can leave it blank. A non-empty value must be one line.
    """
    if origin_ref is None:
        return None
    if not isinstance(origin_ref, str):
        raise ValueError("origin_ref must be a string")
    ref = origin_ref.strip()
    if not ref:
        return None
    if len(ref) > ORIGIN_REF_MAX or any(c in ref for c in "\r\n\x00"):
        raise ValueError("origin_ref must be a single line of at most "
                         f"{ORIGIN_REF_MAX} characters")
    return ref


def find_by_origin_ref(vault: Vault, origin_ref: str) -> pathlib.Path | None:
    """First note (by path) whose frontmatter origin_ref matches. Read-only."""
    matches = []
    root = vault.root
    for rel in vault.notes():
        try:
            resolved = (root / rel).resolve()
        except OSError:
            continue
        if not resolved.is_relative_to(root):
            continue
        try:
            text = resolved.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta, _ = parse_frontmatter(text)
        existing = meta.get("origin_ref")
        if existing is None:
            continue
        if str(existing).strip() == origin_ref:
            matches.append(rel)
    if not matches:
        return None
    return sorted(matches, key=str)[0]


def _append_log(vault: Vault, entry: dict) -> None:
    log_path = vault.root / LOG_REL
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _read_existing(vault: Vault, rel: pathlib.Path) -> dict:
    try:
        return vault.read(str(rel))
    except (ValueError, OSError, FileNotFoundError) as exc:
        return {"path": str(rel), "error": str(exc)}


def _slug_ok(slug: str) -> bool:
    return bool(slug) and not any(c in slug for c in "/\\\r\n\x00") and slug not in {".", ".."} and ".." not in slug


def _normalize_contests(vault: Vault, contests) -> list[str]:
    """Read-only check that each contested slug already exists. Writes nothing."""
    if contests is None:
        return []
    if not isinstance(contests, list):
        raise ValueError("contests must be a list of note slugs")
    out = []
    seen = set()
    for item in contests:
        if not isinstance(item, str):
            raise ValueError("each contested slug must be a string")
        slug = item.strip()
        if not _slug_ok(slug):
            raise ValueError(f"contested slug must be a single slug: {item!r}")
        key = slug.casefold()
        if key in seen:
            continue
        seen.add(key)
        try:
            vault.read(slug)
        except FileNotFoundError as exc:
            raise ValueError(f"no note to contest: {slug}") from exc
        out.append(slug)
    return out


def _lifecycle_status(status, contests: list[str], fallback: str) -> str:
    """Pick the status stored on a new note. ``fallback`` is the write-dir name."""
    if status is None or (isinstance(status, str) and not status.strip()):
        chosen = None
    elif not isinstance(status, str):
        raise ValueError("status must be a string")
    else:
        chosen = status.strip().casefold()
        if chosen not in LIFECYCLE_STATUSES:
            raise ValueError(
                "status must be one of " + ", ".join(LIFECYCLE_STATUSES)
                + " when set; omit it to keep the capture default"
            )
    if contests:
        if chosen not in (None, "contested"):
            raise ValueError("a note that contests other slugs uses status contested")
        return "contested"
    if chosen == "contested":
        raise ValueError("status contested requires one or more contests slugs")
    return chosen or fallback


def _normalize_resolution(vault: Vault, resolution, resolves, contests: list[str]):
    if resolution is None and resolves is None:
        return None, None
    if contests:
        raise ValueError("a contested note is not itself a resolution")
    if resolution is None or resolves is None:
        raise ValueError("resolution and resolves are set together")
    if not isinstance(resolution, str) or resolution.strip().casefold() != "proposed":
        raise ValueError("resolution must be proposed; applying it is a human edit")
    if not isinstance(resolves, str) or not _slug_ok(resolves.strip()):
        raise ValueError("resolves must be a slug")
    slug = resolves.strip()
    try:
        vault.read(slug)
    except FileNotFoundError as exc:
        raise ValueError(f"no note to resolve: {slug}") from exc
    return "proposed", slug


def _result_fields(note: dict) -> dict:
    fm = note.get("frontmatter") if isinstance(note.get("frontmatter"), dict) else {}
    contests = fm.get("contests") if isinstance(fm.get("contests"), list) else []
    return {
        "status": None if fm.get("status") is None else str(fm.get("status")),
        "contests": [str(s) for s in contests],
        "resolution": None if fm.get("resolution") is None else str(fm.get("resolution")),
        "resolves": None if fm.get("resolves") is None else str(fm.get("resolves")),
    }


def capture_note(
    vault: Vault,
    title: str,
    body: str,
    sources: list[str] | None = None,
    agent: str = "mcp",
    origin_ref: str | None = None,
    status: str | None = None,
    contests: list[str] | None = None,
    resolution: str | None = None,
    resolves: str | None = None,
) -> dict:
    """File a new note into the governed write dir (default ``inbox/``).

    Never overwrites or edits an existing note. When ``origin_ref`` matches a
    note already in the vault, return that note (``created: false``) and do
    not write a second file. Two concurrent callers can both miss the lookup;
    a later call still will not edit either file — it returns the
    lexicographically first match.

    ``contests`` names existing slugs the new evidence disagrees with. The new
    note is ``status: contested`` and the named notes are only read. ``status``
    may also be ``active``, ``stale``, or ``archived`` on that new note. Omit
    both and the note keeps the previous default (the write-dir name).
    """
    if "/" in title or "\\" in title or ".." in title:
        raise PermissionError(f"title must not contain path separators: {title!r}")
    ref = _normalize_origin_ref(origin_ref)
    named = _normalize_contests(vault, contests)
    if named and not str(body or "").strip():
        raise ValueError("contested capture needs the conflicting evidence in body")
    wd = write_dir(vault.root)
    chosen = _lifecycle_status(status, named, wd)
    resolution, resolves_slug = _normalize_resolution(vault, resolution, resolves, named)
    now = datetime.datetime.now(datetime.timezone.utc)
    if ref is not None:
        existing = find_by_origin_ref(vault, ref)
        if existing is not None:
            note = _read_existing(vault, existing)
            _append_log(vault, {
                "ts": now.isoformat(),
                "agent": agent,
                "action": "capture_note_idempotent",
                "path": str(existing),
                "title": title,
                "origin_ref": ref,
            })
            return {
                "path": str(existing),
                "logged": True,
                "created": False,
                "idempotent": True,
                "origin_ref": ref,
                "note": note,
                **_result_fields(note),
            }

    target_dir = (vault.root / wd).resolve()
    if not target_dir.is_relative_to(vault.root):
        raise PermissionError(f"write dir escapes vault: {wd}")
    slug = _slugify(title)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    target_dir.mkdir(parents=True, exist_ok=True)
    rel = None
    for i in itertools.count():
        name = f"{slug}-{stamp}.md" if i == 0 else f"{slug}-{stamp}-{i}.md"
        cand = target_dir / name
        if cand.resolve().parent != target_dir:
            raise PermissionError(f"write escapes boundary: {name}")
        if not cand.exists():
            rel = cand.relative_to(vault.root)
            frontmatter = {
                "title": title,
                "status": chosen,
                "captured_by": agent,
                "captured_at": now.isoformat(),
                "sources": sources or [],
            }
            if ref is not None:
                frontmatter["origin_ref"] = _QuotedStr(ref)
            if named:
                frontmatter["contests"] = [_QuotedStr(s) for s in named]
            if resolution is not None:
                frontmatter["resolution"] = _QuotedStr(resolution)
                frontmatter["resolves"] = _QuotedStr(resolves_slug)
            cand.write_text(
                "---\n" + yaml.safe_dump(frontmatter, sort_keys=False) + "---\n\n" + body.rstrip() + "\n",
                encoding="utf-8",
            )
            break
    entry = {
        "ts": now.isoformat(),
        "agent": agent,
        "action": "capture_note",
        "path": str(rel),
        "title": title,
        "sources": sources or [],
        "status": chosen,
    }
    if ref is not None:
        entry["origin_ref"] = ref
    if named:
        entry["contests"] = named
    if resolves_slug is not None:
        entry["resolves"] = resolves_slug
    _append_log(vault, entry)
    return {
        "path": str(rel),
        "logged": True,
        "created": True,
        "idempotent": False,
        "origin_ref": ref,
        "status": chosen,
        "contests": named,
        "resolution": resolution,
        "resolves": resolves_slug,
    }


def propose_resolution(
    vault: Vault,
    contest: str,
    proposal: str,
    sources: list[str] | None = None,
    agent: str = "mcp",
    origin_ref: str | None = None,
) -> dict:
    """File a new inbox note that proposes how a human might resolve a conflict.

    Reads the contested note and the notes it names. Does not edit any of them.
    The new note is ``resolution: proposed``. Applying that proposal — changing
    any existing note — is a human edit, not this function.
    """
    if not isinstance(contest, str) or not _slug_ok(contest.strip()):
        raise ValueError("contest must be the slug of a contested note")
    slug = contest.strip()
    try:
        note = vault.read(slug)
    except FileNotFoundError as exc:
        raise ValueError(f"no contested note: {slug}") from exc
    fm = note.get("frontmatter") if isinstance(note.get("frontmatter"), dict) else {}
    if str(fm.get("status") or "").strip().casefold() != "contested":
        raise ValueError(f"{slug} is not status contested")
    raw = fm.get("contests")
    if not isinstance(raw, list) or not [str(s).strip() for s in raw if str(s).strip()]:
        raise ValueError(f"{slug} does not name the notes it contests")
    text = "" if proposal is None else str(proposal).strip()
    if not text:
        raise ValueError("proposal text is required")
    contest_slug = pathlib.Path(note["path"]).stem
    title_src = str(fm.get("title") or contest_slug).replace("/", " ").replace("\\", " ")
    title = f"Resolution proposal: {title_src}"[:180]
    cited = ", ".join(f"[[{s}]]" for s in raw)
    excerpt = " ".join(str(note.get("body") or "").split())[:400]
    body = (
        f"Proposed resolution for [[{contest_slug}]].\n\n"
        "A human approves this note before anything changes. "
        "Filing it does not edit the contested note or the notes it disputes.\n\n"
        f"Contested notes: {cited}\n\n"
        f"Evidence on file: {excerpt}\n\n"
        "## Proposal\n\n"
        f"{text}\n"
    )
    return capture_note(
        vault, title, body, sources=sources, agent=agent, origin_ref=origin_ref,
        status="active", resolution="proposed", resolves=contest_slug,
    )
