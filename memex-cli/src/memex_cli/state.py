"""Incremental ingest state — a resumable cursor, never a source of truth.

Deleting `.memex/ingest_state.json` loses nothing except dedup memory; the vault
remains canonical (invariant 1).
"""
from __future__ import annotations

import hashlib
import json
import pathlib

STATE_REL = pathlib.Path(".memex") / "ingest_state.json"


def url_key(url: str) -> str:
    return hashlib.sha256(url.strip().rstrip("/").encode("utf-8")).hexdigest()[:24]


class IngestState:
    def __init__(self, vault_root: pathlib.Path):
        self.path = vault_root / STATE_REL
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = {}
        self.data.setdefault("url", {})

    def seen_url(self, url: str) -> dict | None:
        return self.data["url"].get(url_key(url))

    def record_url(self, url: str, note_path: str, fetched_at: str) -> None:
        self.data["url"][url_key(url)] = {
            "url": url, "note": note_path, "fetched_at": fetched_at,
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
