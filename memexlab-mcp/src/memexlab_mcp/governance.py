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


def capture_note(
    vault: Vault,
    title: str,
    body: str,
    sources: list[str] | None = None,
    agent: str = "mcp",
    origin_ref: str | None = None,
) -> dict:
    """File a new note into the governed write dir (default ``inbox/``).

    Never overwrites or edits an existing note. When ``origin_ref`` matches a
    note already in the vault, return that note (``created: false``) and do
    not write a second file. Two concurrent callers can both miss the lookup;
    a later call still will not edit either file — it returns the
    lexicographically first match.
    """
    if "/" in title or "\\" in title or ".." in title:
        raise PermissionError(f"title must not contain path separators: {title!r}")
    ref = _normalize_origin_ref(origin_ref)
    now = datetime.datetime.now(datetime.timezone.utc)
    if ref is not None:
        existing = find_by_origin_ref(vault, ref)
        if existing is not None:
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
                "note": _read_existing(vault, existing),
            }

    wd = write_dir(vault.root)
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
                "status": wd,
                "captured_by": agent,
                "captured_at": now.isoformat(),
                "sources": sources or [],
            }
            if ref is not None:
                frontmatter["origin_ref"] = _QuotedStr(ref)
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
    }
    if ref is not None:
        entry["origin_ref"] = ref
    _append_log(vault, entry)
    return {
        "path": str(rel),
        "logged": True,
        "created": True,
        "idempotent": False,
        "origin_ref": ref,
    }
