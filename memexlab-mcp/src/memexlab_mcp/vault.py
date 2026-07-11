"""Read layer over a plain-markdown vault. No writes here — see governance.py."""
from __future__ import annotations

import pathlib

import yaml

MAX_NOTE_BYTES = 2_000_000
_EXCLUDED_TOP = {".memexlab"}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            raw = text[4:end]
            body = text[end + 5 :]
            try:
                meta = yaml.safe_load(raw) or {}
            except yaml.YAMLError:
                return {}, text
            return (meta if isinstance(meta, dict) else {}), body
    return {}, text


class Vault:
    def __init__(self, root: pathlib.Path):
        self.root = pathlib.Path(root).resolve()
        if not self.root.is_dir():
            raise ValueError(f"vault root is not a directory: {root}")

    def notes(self) -> list[pathlib.Path]:
        out = []
        for p in self.root.rglob("*.md"):
            rel = p.relative_to(self.root)
            if rel.parts and rel.parts[0] in _EXCLUDED_TOP:
                continue
            out.append(rel)
        return sorted(out)

    def read(self, ref: str) -> dict:
        rel = self._resolve(ref)
        full = self.root / rel
        if full.stat().st_size > MAX_NOTE_BYTES:
            raise ValueError(f"note too large: {rel}")
        meta, body = parse_frontmatter(full.read_text(encoding="utf-8", errors="replace"))
        return {"path": str(rel), "frontmatter": meta, "body": body}

    def _resolve(self, ref: str) -> pathlib.Path:
        cand = self.root / ref
        if cand.is_file() and cand.resolve().is_relative_to(self.root):
            return pathlib.Path(ref)
        want = ref.casefold()
        for rel in self.notes():
            if rel.stem.casefold() == want:
                if (self.root / rel).resolve().is_relative_to(self.root):
                    return rel
        raise FileNotFoundError(f"no note matches: {ref}")
