"""Vault-scoped tools — the only ways the agent can touch the workspace.

Containment, precisely:

* ``read_file`` and ``write_file`` resolve their path against the vault root and
  refuse anything that lands outside it (symlinks included, since the path is
  resolved before the check).
* ``list_files`` rejects glob patterns that are absolute or contain ``..``, and
  drops any match that resolves outside the root.
* ``search`` skips any file that resolves outside the root, so a symlink planted
  in the vault cannot pull outside content into the model's context.
* ``write_file`` is the single mutating op. It writes only inside the vault's
  governance-defined write dir (``write_dir`` in the vault's ``governance.yml``,
  default ``inbox``), never overwrites an existing file, and appends an entry to
  ``.memexlab/log.jsonl`` — the same boundary and audit trail memexlab-mcp's
  governance.capture_note enforces. Canonical notes are therefore append-only
  from the agent's side: a poisoned note it reads back cannot make it blank one.

If PyYAML is not installed the write dir falls back to the default ``inbox``
rather than reading ``governance.yml`` — fail-closed, since the default is the
most restrictive choice.
"""
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys

try:  # optional: the runner stays usable on a bare stdlib install
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised by env, not tests
    yaml = None

DEFAULT_WRITE_DIR = "inbox"
LOG_REL = pathlib.Path(".memexlab") / "log.jsonl"
_SEP = re.compile(r"[\\/]+")


class Workspace:
    """The agent's working directory: a markdown vault."""

    def __init__(self, root, agent="runner"):
        self.root = pathlib.Path(root).expanduser().resolve()
        self.agent = agent
        if not self.root.is_dir():
            raise SystemExit("workspace not found: {}".format(self.root))

    # --- internal -----------------------------------------------------------
    def _resolve(self, rel):
        p = (self.root / rel).resolve()
        if not (p == self.root or str(p).startswith(str(self.root) + os.sep)):
            raise ValueError("path escapes workspace: {}".format(rel))
        return p

    def _inside(self, p):
        """True if p, fully resolved, is the root or lives under it."""
        try:
            rp = p.resolve()
        except OSError:
            return False
        return rp == self.root or str(rp).startswith(str(self.root) + os.sep)

    def _check_glob(self, pattern):
        if not isinstance(pattern, str) or not pattern.strip():
            raise ValueError("glob pattern must be a non-empty string")
        if pattern.startswith(("/", "\\")) or os.path.isabs(pattern):
            raise ValueError("absolute glob pattern is not allowed: {}".format(pattern))
        if ".." in _SEP.split(pattern):
            raise ValueError("glob pattern escapes workspace: {}".format(pattern))
        return pattern

    def write_dir(self):
        """The one directory the agent may write into, per vault governance."""
        gov = self.root / "governance.yml"
        if yaml is not None and gov.is_file():
            try:
                data = yaml.safe_load(gov.read_text(encoding="utf-8")) or {}
                if isinstance(data, dict):
                    wd = data.get("write_dir")
                    if isinstance(wd, str) and wd.strip():
                        return wd.strip()
            except (yaml.YAMLError, OSError):
                pass
        return DEFAULT_WRITE_DIR

    def _log(self, action, path, **extra):
        log_path = self.root / LOG_REL
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "agent": self.agent,
            "action": action,
            "path": path,
        }
        entry.update(extra)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # --- tools --------------------------------------------------------------
    def list_files(self, glob="**/*.md"):
        self._check_glob(glob)
        return sorted(
            str(p.relative_to(self.root))
            for p in self.root.glob(glob)
            if p.is_file() and self._inside(p)
        )

    def read_file(self, path):
        return self._resolve(path).read_text(encoding="utf-8")

    def write_file(self, path, content):
        p = self._resolve(path)
        wd = self.write_dir()
        target_dir = (self.root / wd).resolve()
        if not self._inside(target_dir) or target_dir == self.root:
            raise PermissionError("write dir escapes vault: {}".format(wd))
        if p == target_dir or not str(p).startswith(str(target_dir) + os.sep):
            raise PermissionError(
                "writes are confined to {}/ — refused: {}".format(wd, path))
        if p.exists() or p.is_symlink():
            raise PermissionError(
                "refusing to overwrite an existing file: {}".format(path))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        rel = str(p.relative_to(self.root))
        self._log("write_file", rel, bytes=len(content))
        return "wrote {} ({} bytes)".format(rel, len(content))

    def search(self, query, limit=20):
        hits = []
        q = query.lower()
        for p in sorted(self.root.rglob("*.md")):
            if not self._inside(p):
                continue
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
