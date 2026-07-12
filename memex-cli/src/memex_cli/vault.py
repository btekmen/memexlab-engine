"""Vault resolution, read layer, and the governed write boundary (mirrors
memexlab-mcp semantics — same frontmatter parse, same exclusions)."""
from __future__ import annotations

import pathlib

import yaml

DEFAULT_WRITE_DIR = "inbox"
MAX_NOTE_BYTES = 2_000_000
_EXCLUDED_TOP = {".memexlab", ".memex", ".obsidian", ".git"}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            raw = text[4:end]
            body = text[end + 5:]
            try:
                meta = yaml.safe_load(raw) or {}
            except yaml.YAMLError:
                return {}, text
            return (meta if isinstance(meta, dict) else {}), body
    return {}, text


class Vault:
    def __init__(self, root: str | pathlib.Path):
        self.root = pathlib.Path(root).resolve()
        if not self.root.is_dir():
            raise ValueError(f"vault root is not a directory: {root}")

    def write_dir(self) -> str:
        gov = self.root / "governance.yml"
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

    def notes(self) -> list[pathlib.Path]:
        out = []
        for p in self.root.rglob("*.md"):
            rel = p.relative_to(self.root)
            if rel.parts and rel.parts[0] in _EXCLUDED_TOP:
                continue
            out.append(rel)
        return sorted(out)

    def read(self, rel: str | pathlib.Path) -> dict:
        full = (self.root / rel).resolve()
        if not full.is_relative_to(self.root) or not full.is_file():
            raise FileNotFoundError(f"no note at: {rel}")
        if full.stat().st_size > MAX_NOTE_BYTES:
            raise ValueError(f"note too large: {rel}")
        meta, body = parse_frontmatter(full.read_text(encoding="utf-8", errors="replace"))
        return {"path": str(pathlib.Path(rel)), "frontmatter": meta, "body": body}

    def write_target(self) -> pathlib.Path:
        target = (self.root / self.write_dir()).resolve()
        if not target.is_relative_to(self.root):
            raise PermissionError(f"write dir escapes vault: {self.write_dir()}")
        return target
