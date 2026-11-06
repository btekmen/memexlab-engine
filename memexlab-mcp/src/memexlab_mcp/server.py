"""memexlab-mcp — governed, citable, local memory for AI agents (stdio MCP)."""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

from mcp.server.fastmcp import FastMCP

from . import governance, queue as queue_mod, views
from .meter import record as meter_record
from .plasticity import score_plasticity
from .prompt_index import build_prompt_index
from .search import search as _search
from .vault import Vault

mcp = FastMCP("memexlab")
_vault: Vault | None = None


def configure(path: str) -> None:
    global _vault
    _vault = Vault(path)  # raises ValueError on bad path


def _require_vault() -> Vault:
    if _vault is None:
        raise RuntimeError("vault not configured — pass --vault or set MEMEXLAB_VAULT")
    return _vault


def _meter(vault: Vault, *, route: str, text: str, cited_slugs: list[str], query: str = "") -> None:
    """Record a retrieval. A meter failure must not fail the tool."""
    try:
        meter_record(vault.root, route=route, text=text, cited_slugs=cited_slugs, query=query)
    except (OSError, ValueError, PermissionError):
        return


@mcp.tool()
def vault_info() -> dict:
    """Vault overview: note count, top-level sections, and the governed write dir."""
    v = _require_vault()
    notes = v.notes()
    sections: dict[str, int] = {}
    for rel in notes:
        sections[rel.parts[0]] = sections.get(rel.parts[0], 0) + 1
    return {
        "root": str(v.root),
        "notes": len(notes),
        "sections": sections,
        "write_dir": governance.write_dir(v.root),
        "views": [w["name"] for w in views.list_views(v)],
    }


@mcp.tool()
def get_index(limit: int = 200, section: str | None = None) -> dict:
    """Compact prompt index of the vault: one line per note, no bodies.

    Each line is `[[slug]] | title | section | type | status` (empty type and
    status are omitted). Contested notes are listed first and name the slugs
    they contest. Use search_vault to find candidates and read_note to pull a
    body. `section` is an optional top-level folder name, for example
    "concepts". `status` is copied from frontmatter when a note already has it.
    """
    v = _require_vault()
    idx = build_prompt_index(v, limit=limit, section=section)
    _meter(
        v, route="mcp.get_index", text=idx["prompt"],
        cited_slugs=[n["slug"] for n in idx["notes"]], query=section or "",
    )
    return idx


@mcp.tool()
def search_vault(query: str = "", limit: int = 5, view: str | None = None) -> list[dict]:
    """Deterministic BM25 search. Cite results as [[slug]].

    Each hit includes status (empty when the note has none). A contested hit
    also includes contests, the slugs the note disagrees with.

    Pass `view` (a name from views/) to scope the corpus to that saved query;
    with an empty `query` the view's members are listed (using the view's own
    `text` field as the query when it has one)."""
    v = _require_vault()
    if view is None:
        hits = _search(v, query, limit=limit)
    else:
        member_paths = views.members(v, view)
        q = query or views.load_view(v, view)["text"]
        if not q:
            hits = []
            for p in member_paths[:limit]:
                hit = {"slug": p.stem, "path": str(p), "score": 0.0, "snippet": "", "status": ""}
                try:
                    fm = v.read(str(p)).get("frontmatter") or {}
                except (ValueError, OSError, FileNotFoundError):
                    fm = {}
                if isinstance(fm, dict) and isinstance(fm.get("status"), str):
                    hit["status"] = fm["status"].strip()
                contests = fm.get("contests") if isinstance(fm, dict) else None
                if isinstance(contests, list) and contests:
                    hit["contests"] = [str(s) for s in contests]
                hits.append(hit)
        else:
            hits = _search(v, q, limit=limit, allowed={str(p) for p in member_paths})
    _meter(
        v, route="mcp.search_vault",
        text="\n".join(f"[[{h['slug']}]] {h.get('snippet', '')}" for h in hits),
        cited_slugs=[h["slug"] for h in hits], query=query or (view or ""),
    )
    return hits


@mcp.tool()
def read_note(note: str) -> dict:
    """Read one note by slug or relative path; returns frontmatter + body."""
    v = _require_vault()
    found = v.read(note)
    _meter(
        v, route="mcp.read_note", text=found.get("body") or "",
        cited_slugs=[pathlib.Path(found["path"]).stem], query=note,
    )
    return found


@mcp.tool()
def capture_note(title: str, body: str, sources: list[str] | None = None,
                 origin_ref: str | None = None, status: str | None = None,
                 contests: list[str] | None = None) -> dict:
    """Governed write: files a new note into the write dir (default inbox/).

    Never overwrites or edits an existing note. Pass origin_ref to make the
    write idempotent — the same origin_ref returns the existing note and does
    not create a duplicate. Canonical notes can never be modified.

    When new information conflicts with an existing note, pass contests as the
    slugs it disagrees with and put the evidence in body. That files a new
    inbox note with status contested and leaves the named notes byte-for-byte
    unchanged. status may also be active, stale, or archived on the new note.
    Omit status and contests to keep the previous capture behavior.
    """
    return governance.capture_note(
        _require_vault(), title, body, sources=sources,
        agent="memexlab-mcp", origin_ref=origin_ref, status=status,
        contests=contests)


@mcp.tool()
def propose_resolution(contest: str, proposal: str, sources: list[str] | None = None,
                       origin_ref: str | None = None) -> dict:
    """File a proposed resolution for a contested note. Does not edit any note.

    contest is the slug of a note with status contested. The new inbox note is
    resolution: proposed and waits for a human to approve it. The same
    origin_ref returns that proposal instead of writing another one.
    """
    return governance.propose_resolution(
        _require_vault(), contest, proposal, sources=sources,
        agent="memexlab-mcp", origin_ref=origin_ref)


@mcp.tool()
def plasticity(policy: str = "all", limit: int = 0) -> dict:
    """Read-only re-entry (rps) and promotion (mws) scores from plasticity.yml.

    Every score includes a per-factor breakdown. rps ranks notes for a morning
    brief. mws recommends which inbox notes a human might promote and does not
    move them. limit 0 uses the policy file's limit. This tool does not edit
    notes, move files, or use the network.
    """
    return score_plasticity(
        _require_vault(), policy, limit=None if limit < 1 else limit,
    )


@mcp.tool()
def list_queue(status: str = "pending") -> list[dict]:
    """Read-only view of the vault's task queue (queue/*.md notes).
    status: pending | claimed | done | cancelled | all."""
    return queue_mod.list_queue(_require_vault(), status=status)


@mcp.tool()
def complete_queue_item(item: str, result_title: str, result_body: str,
                        sources: list[str] | None = None) -> dict:
    """Complete a queue item. Files the result as a governed note in the write
    dir (provenance + JSONL log) and only then marks the item done, linking the
    result. Call this ONLY after genuinely finishing the task — an empty result
    is refused, and no other status transition is reachable from here."""
    return queue_mod.complete_queue_item(
        _require_vault(), item, result_title, result_body,
        sources=sources, agent="memexlab-mcp")


def main() -> None:
    parser = argparse.ArgumentParser(prog="memexlab-mcp", description=__doc__)
    parser.add_argument("--vault", default=os.environ.get("MEMEXLAB_VAULT"),
                        help="path to the markdown vault (or set MEMEXLAB_VAULT)")
    args = parser.parse_args()
    if not args.vault:
        parser.error("--vault is required (or set MEMEXLAB_VAULT)")
    try:
        configure(args.vault)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        raise SystemExit(2)
    mcp.run()


if __name__ == "__main__":
    main()
