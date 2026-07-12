"""Vault resolution and the governed write boundary (mirrors memexlab-mcp semantics)."""
from __future__ import annotations

import pathlib

import yaml

DEFAULT_WRITE_DIR = "inbox"


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

    def write_target(self) -> pathlib.Path:
        target = (self.root / self.write_dir()).resolve()
        if not target.is_relative_to(self.root):
            raise PermissionError(f"write dir escapes vault: {self.write_dir()}")
        return target
