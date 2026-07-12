"""The 60-second wow, scripted: search → cited answer → governed capture → proof."""
from __future__ import annotations

import argparse
import hashlib
import pathlib

from . import server
from .governance import write_dir
from .vault import Vault


def _canonical_digest(root: pathlib.Path) -> str:
    wd = write_dir(root)
    h = hashlib.sha256()
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root)
        if rel.parts and rel.parts[0] in {wd, ".memexlab"}:
            continue
        h.update(str(rel).encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def run_demo(vault_path: str, out=print) -> dict:
    server.configure(vault_path)
    root = Vault(vault_path).root
    info = server.vault_info()
    out(f"▸ vault: {info['notes']} notes in {sorted(info['sections'])} — write dir: {info['write_dir']}/")

    first = server._require_vault().notes()[0]
    query = first.stem.split("-")[0]
    hits = server.search_vault(query, limit=3)
    out(f"▸ search_vault({query!r}) → {len(hits)} hits (deterministic, citable):")
    for h in hits:
        out(f"    [[{h['slug']}]]  {h['path']}  score={h['score']}")

    before = _canonical_digest(root)
    cited = [h["slug"] for h in hits[:2]]
    res = server.capture_note(
        "Demo capture — agent memory that cannot corrupt",
        f"Captured by the demo. Cited: {', '.join(f'[[{s}]]' for s in cited)}.",
        sources=cited,
    )
    changed = _canonical_digest(root) != before
    out(f"▸ capture_note(...) → {res['path']}  (provenance frontmatter + log entry)")
    out(f"▸ canonical layer changed: {changed}  ← governance enforced in code")
    out(f"▸ write log: .memexlab/log.jsonl")
    return {"hits": len(hits), "captured": res["path"], "canonical_changed": changed}


def main() -> None:
    parser = argparse.ArgumentParser(prog="memexlab-mcp-demo")
    parser.add_argument("--vault", required=True)
    args = parser.parse_args()
    run_demo(args.vault)


if __name__ == "__main__":
    main()
