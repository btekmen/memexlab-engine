"""Governed agent task queue — queue items are notes; completion is checked in code.

A queue item is a markdown note in the vault's queue dir (default ``queue/``,
configurable via ``queue_dir:`` in the vault's governance.yml) with frontmatter
``type: queue-item`` and a ``status`` of ``pending | claimed | done | cancelled``.
Humans create and cancel items in any editor; agents may only *list* items and
*complete* them.

The anti-fake-completion contract, enforced here rather than by convention:
completing an item REQUIRES filing a result note (which lands in the governed
write dir with provenance, like any capture). The status flip and the result
note happen in one call, the item links its result, and both writes are logged
to ``.memexlab/log.jsonl``. There is no agent-reachable code path that deletes
an item, edits its body, or moves it to any status other than ``done``.
"""
from __future__ import annotations

import datetime
import json
import pathlib

import yaml

from . import governance
from .vault import Vault, parse_frontmatter

DEFAULT_QUEUE_DIR = "queue"
STATUSES = ("pending", "claimed", "done", "cancelled")
COMPLETABLE = ("pending", "claimed")


def queue_dir(vault_root: pathlib.Path) -> str:
    gov = pathlib.Path(vault_root) / "governance.yml"
    if gov.is_file():
        try:
            data = yaml.safe_load(gov.read_text(encoding="utf-8")) or {}
            if isinstance(data, dict):
                qd = data.get("queue_dir")
                if isinstance(qd, str) and qd.strip():
                    return qd.strip()
        except yaml.YAMLError:
            pass
    return DEFAULT_QUEUE_DIR


def _item_path(vault: Vault, item: str) -> pathlib.Path:
    qd = queue_dir(vault.root)
    rel = pathlib.Path(qd) / f"{pathlib.Path(item).name}.md"
    full = (vault.root / rel).resolve()
    if not full.is_relative_to(vault.root):
        raise PermissionError(f"queue dir escapes vault: {qd}")
    if not full.is_file():
        raise ValueError(f"no queue item named '{item}' (expected {rel})")
    return rel


def _load(vault: Vault, rel: pathlib.Path) -> tuple[dict, str]:
    meta, body = parse_frontmatter((vault.root / rel).read_text(encoding="utf-8"))
    if meta.get("type") != "queue-item":
        raise ValueError(f"{rel} is not a queue item (frontmatter must set 'type: queue-item')")
    return meta, body


def list_queue(vault: Vault, status: str = "pending") -> list[dict]:
    """Read-only listing. status: one of pending|claimed|done|cancelled|all."""
    if status not in STATUSES + ("all",):
        raise ValueError(f"status must be one of {', '.join(STATUSES + ('all',))}")
    qd = queue_dir(vault.root)
    out = []
    for rel in vault.notes():
        if rel.parts[0] != qd or len(rel.parts) != 2:
            continue
        try:
            meta, body = _load(vault, rel)
        except ValueError:
            continue
        st = str(meta.get("status", "pending"))
        if status != "all" and st != status:
            continue
        out.append({
            "item": rel.stem,
            "path": str(rel),
            "title": str(meta.get("title", rel.stem)),
            "status": st,
            "destination": str(meta.get("destination", "")),
            "created": str(meta.get("created", "")),
            "task": body.strip()[:500],
        })
    return sorted(out, key=lambda r: (r["created"], r["item"]))


def complete_queue_item(
    vault: Vault,
    item: str,
    result_title: str,
    result_body: str,
    sources: list[str] | None = None,
    agent: str = "memexlab-mcp",
) -> dict:
    """File a result note (governed write), then mark the item done, atomically-ish.

    Refuses when the item is not pending/claimed, or when the result is empty —
    an agent cannot mark work done without producing the work.
    """
    if not result_title.strip() or not result_body.strip():
        raise ValueError("completion requires a non-empty result note (title and body)")
    rel = _item_path(vault, item)
    meta, body = _load(vault, rel)
    st = str(meta.get("status", "pending"))
    if st not in COMPLETABLE:
        raise ValueError(f"queue item '{rel.stem}' is '{st}' — only {' / '.join(COMPLETABLE)} can be completed")

    result = governance.capture_note(
        vault, result_title, result_body,
        sources=list(dict.fromkeys((sources or []) + [rel.stem])), agent=agent,
    )

    # compare-and-set: re-read, then flip status; refuse if it changed underneath us
    meta2, body2 = _load(vault, rel)
    if str(meta2.get("status", "pending")) != st:
        raise ValueError(f"queue item '{rel.stem}' changed status concurrently; result note kept at {result['path']}")
    now = datetime.datetime.now(datetime.timezone.utc)
    meta2.update({"status": "done", "completed_at": now.isoformat(),
                  "completed_by": agent, "result": result["path"]})
    (vault.root / rel).write_text(
        "---\n" + yaml.safe_dump(meta2, sort_keys=False) + "---\n" + body2,
        encoding="utf-8",
    )
    log_path = vault.root / governance.LOG_REL
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": now.isoformat(), "agent": agent, "action": "complete_queue_item",
            "path": str(rel), "result": result["path"],
        }, ensure_ascii=False) + "\n")
    return {"item": rel.stem, "path": str(rel), "status": "done", "result": result["path"], "logged": True}
