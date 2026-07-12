"""Views — named, reusable query scopes stored as plain notes in views/*.md.

A view is a markdown note whose frontmatter declares `type: view` and a `query:`
block. Evaluation is deterministic and read-only: AND across fields, OR within a
list field. The view file is vault content like any other note — shareable by
sharing the file.

Recognised query fields:
  tags        all listed tags must be present
  any_tags    at least one listed tag present
  not_tags    none of the listed tags present
  types       frontmatter `type` is one of these
  statuses    frontmatter `status` is one of these
  folders     note's top-level folder is one of these
  since/until ISO date bounds against `date`/`created`/`updated` (first present)
  text        default BM25 query when the caller supplies none

Unknown query fields are errors (strict-schema discipline).
"""
from __future__ import annotations

import datetime
import pathlib

from .vault import Vault

VIEWS_DIR = "views"
_LIST_FIELDS = {"tags", "any_tags", "not_tags", "types", "statuses", "folders"}
_SCALAR_FIELDS = {"since", "until", "text"}
QUERY_FIELDS = _LIST_FIELDS | _SCALAR_FIELDS


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(x) for x in value]
    return [str(value)]


def _iso(value) -> str:
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()[:10]
    return str(value)[:10]


def list_views(vault: Vault) -> list[dict]:
    """Every valid view in views/, sorted by name."""
    out = []
    for rel in vault.notes():
        if rel.parts[0] != VIEWS_DIR or len(rel.parts) != 2:
            continue
        try:
            view = load_view(vault, rel.stem)
        except ValueError:
            continue
        out.append({"name": rel.stem, "title": view.get("title", rel.stem)})
    return sorted(out, key=lambda v: v["name"])


def load_view(vault: Vault, name: str) -> dict:
    """Load and validate one view; returns {'title':…, 'query': {…}}."""
    rel = pathlib.Path(VIEWS_DIR) / f"{pathlib.Path(name).name}.md"
    try:
        note = vault.read(str(rel))
    except FileNotFoundError:
        raise ValueError(f"no view named '{name}' (expected {rel})")
    meta = note["frontmatter"]
    if meta.get("type") != "view":
        raise ValueError(f"{rel} is not a view (frontmatter must set 'type: view')")
    query = meta.get("query") or {}
    if not isinstance(query, dict):
        raise ValueError(f"{rel}: 'query:' must be a mapping")
    unknown = set(query) - QUERY_FIELDS
    if unknown:
        raise ValueError(f"{rel}: unknown query fields: {', '.join(sorted(unknown))}")
    return {"title": str(meta.get("title", name)), "query": query,
            "text": str(query.get("text", "")) if query.get("text") else ""}


def members(vault: Vault, name: str) -> list[pathlib.Path]:
    """Deterministic member list for a view (view files themselves excluded)."""
    query = load_view(vault, name)["query"]
    tags_all = _as_list(query.get("tags"))
    tags_any = _as_list(query.get("any_tags"))
    tags_not = _as_list(query.get("not_tags"))
    types = _as_list(query.get("types"))
    statuses = _as_list(query.get("statuses"))
    folders = _as_list(query.get("folders"))
    since = _iso(query["since"]) if query.get("since") else ""
    until = _iso(query["until"]) if query.get("until") else ""

    out = []
    for rel in vault.notes():
        if rel.parts[0] == VIEWS_DIR:
            continue
        try:
            meta = vault.read(str(rel))["frontmatter"]
        except (ValueError, OSError, FileNotFoundError):
            continue
        note_tags = _as_list(meta.get("tags"))
        if tags_all and not all(t in note_tags for t in tags_all):
            continue
        if tags_any and not any(t in note_tags for t in tags_any):
            continue
        if tags_not and any(t in note_tags for t in tags_not):
            continue
        if types and str(meta.get("type", "")) not in types:
            continue
        if statuses and str(meta.get("status", "")) not in statuses:
            continue
        if folders and rel.parts[0] not in folders:
            continue
        if since or until:
            raw = meta.get("date") or meta.get("created") or meta.get("updated")
            if raw is None:
                continue
            d = _iso(raw)
            if since and d < since:
                continue
            if until and d > until:
                continue
        out.append(rel)
    return sorted(out)
