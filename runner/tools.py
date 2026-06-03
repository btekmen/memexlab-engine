"""Vault-scoped tools — the only ways the agent can touch the workspace.

Every path is resolved against the vault root and guarded against escapes, so the
agent operates *only* inside the workspace it was pointed at. The single mutating
op is write_file; everything else is read-only.
"""
import os
import pathlib
import subprocess
import sys


class Workspace:
    """The agent's working directory: a markdown vault."""

    def __init__(self, root):
        self.root = pathlib.Path(root).expanduser().resolve()
        if not self.root.is_dir():
            raise SystemExit("workspace not found: {}".format(self.root))

    # --- internal -----------------------------------------------------------
    def _resolve(self, rel):
        p = (self.root / rel).resolve()
        if not (p == self.root or str(p).startswith(str(self.root) + os.sep)):
            raise ValueError("path escapes workspace: {}".format(rel))
        return p

    # --- tools --------------------------------------------------------------
    def list_files(self, glob="**/*.md"):
        return sorted(
            str(p.relative_to(self.root))
            for p in self.root.glob(glob)
            if p.is_file()
        )

    def read_file(self, path):
        return self._resolve(path).read_text(encoding="utf-8")

    def write_file(self, path, content):
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return "wrote {} ({} bytes)".format(path, len(content))

    def search(self, query, limit=20):
        hits = []
        q = query.lower()
        for p in sorted(self.root.rglob("*.md")):
            try:
                text = p.read_text(encoding="utf-8")
            except Exception:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if q in line.lower():
                    rel = p.relative_to(self.root)
                    hits.append("{}:{}: {}".format(rel, i, line.strip()[:160]))
                    if len(hits) >= limit:
                        return hits
        return hits

    def validate(self, validate_script):
        if not pathlib.Path(validate_script).exists():
            return "validate script not found: {}".format(validate_script)
        r = subprocess.run(
            [sys.executable, validate_script, str(self.root)],
            capture_output=True, text=True,
        )
        return (r.stdout + r.stderr).strip()

    def stats(self):
        files = self.list_files()
        return {"root": str(self.root), "markdown_files": len(files)}
