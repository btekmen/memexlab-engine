"""The write boundary. Agents may add to the write dir; they can never touch canonical."""
from __future__ import annotations

import datetime
import itertools
import json
import pathlib
import re

import yaml

from .vault import Vault

DEFAULT_WRITE_DIR = "inbox"
LOG_REL = pathlib.Path(".memexlab") / "log.jsonl"


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


def capture_note(
    vault: Vault,
    title: str,
    body: str,
    sources: list[str] | None = None,
    agent: str = "mcp",
) -> dict:
    if "/" in title or "\\" in title or ".." in title:
        raise PermissionError(f"title must not contain path separators: {title!r}")
    wd = write_dir(vault.root)
    target_dir = (vault.root / wd).resolve()
    if not target_dir.is_relative_to(vault.root):
        raise PermissionError(f"write dir escapes vault: {wd}")
    slug = _slugify(title)
    now = datetime.datetime.now(datetime.timezone.utc)
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
            cand.write_text(
                "---\n" + yaml.safe_dump(frontmatter, sort_keys=False) + "---\n\n" + body.rstrip() + "\n",
                encoding="utf-8",
            )
            break
    log_path = vault.root / LOG_REL
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": now.isoformat(),
        "agent": agent,
        "action": "capture_note",
        "path": str(rel),
        "title": title,
        "sources": sources or [],
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {"path": str(rel), "logged": True}
