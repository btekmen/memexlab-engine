"""memexlab-mcp — governed, citable, local memory for AI agents (stdio MCP)."""
from __future__ import annotations

import argparse
import os
import sys

from mcp.server.fastmcp import FastMCP

from . import governance
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
    }


@mcp.tool()
def search_vault(query: str, limit: int = 5) -> list[dict]:
    """Deterministic BM25 search. Cite results as [[slug]]."""
    return _search(_require_vault(), query, limit=limit)


@mcp.tool()
def read_note(note: str) -> dict:
    """Read one note by slug or relative path; returns frontmatter + body."""
    return _require_vault().read(note)


@mcp.tool()
def capture_note(title: str, body: str, sources: list[str] | None = None) -> dict:
    """Governed write: files a note into the vault's write dir (default inbox/)
    with provenance frontmatter. Canonical notes can never be modified."""
    return governance.capture_note(_require_vault(), title, body, sources=sources, agent="memexlab-mcp")


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
