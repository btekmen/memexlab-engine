"""Local retrieval meter — one JSONL record per retrieval, no network.

Keep this module in lockstep with ``memex_cli.meter`` and
``scripts/meter_summary.py``. The record format is the contract.

Each line is a JSON object:

- ``v`` — schema version, ``1``
- ``ts`` — UTC timestamp (ISO-8601)
- ``route`` — which path retrieved (``mcp.search_vault``, ``memex.qa``, …)
- ``retrieved_tokens`` — ``ceil(utf-8 byte length / 4)`` of the text handed back
- ``cited_slugs`` — slugs returned (retrieval) or cited in the answer (``memex.qa``)
- ``hit`` — ``null`` until a later local eval sets ``true`` or ``false``
  (``annotate_hits``)
- ``query`` — optional, single line, truncated

Default file: ``<vault>/.memex/meter.jsonl`` (gitignored with the rest of
``.memex/``). Override with ``MEMEX_METER_PATH`` or ``meter_path:`` in the
vault's ``governance.yml``. An explicit ``path=`` argument wins over both.
"""
from __future__ import annotations

import datetime
import json
import os
import pathlib

import yaml

SCHEMA_VERSION = 1
ENV_VAR = "MEMEX_METER_PATH"
DEFAULT_REL = pathlib.Path(".memex") / "meter.jsonl"
QUERY_MAX = 200
REQUIRED_FIELDS = ("v", "ts", "route", "retrieved_tokens", "cited_slugs", "hit")


def estimate_tokens(text: str) -> int:
    """Deterministic local estimate. Empty text is 0. No tokenizer, no network."""
    if not text:
        return 0
    return (len(text.encode("utf-8")) + 3) // 4


def _governance_meter_path(vault_root: pathlib.Path) -> str:
    gov = vault_root / "governance.yml"
    if not gov.is_file():
        return ""
    try:
        data = yaml.safe_load(gov.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return ""
    if isinstance(data, dict):
        raw = data.get("meter_path")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return ""


def _coerce(vault_root: pathlib.Path, raw) -> pathlib.Path:
    text = str(raw).strip()
    if not text or "://" in text:
        raise ValueError("meter path must be a local file path")
    path = pathlib.Path(text).expanduser()
    if path.is_absolute():
        return path.resolve()
    if ".." in path.parts:
        raise PermissionError("relative meter path must stay inside the vault")
    resolved = (vault_root / path).resolve()
    if not resolved.is_relative_to(vault_root):
        raise PermissionError("meter path escapes the vault")
    return resolved


def resolve_path(vault_root, path=None) -> pathlib.Path:
    """Resolve the JSONL path. ``path`` overrides the env var, which overrides governance."""
    root = pathlib.Path(vault_root).expanduser().resolve()
    if path is not None:
        return _coerce(root, path)
    env = os.environ.get(ENV_VAR, "").strip()
    if env:
        return _coerce(root, env)
    gov = _governance_meter_path(root)
    if gov:
        return _coerce(root, gov)
    return (root / DEFAULT_REL).resolve()


def _slugs(cited_slugs) -> list[str]:
    if isinstance(cited_slugs, str) or not isinstance(cited_slugs, (list, tuple)):
        raise ValueError("cited_slugs must be a list of strings")
    out: list[str] = []
    for slug in cited_slugs:
        text = " ".join(str(slug).split())
        if text and text not in out:
            out.append(text)
    return out


def record(
    vault_root,
    *,
    route: str,
    text: str,
    cited_slugs,
    query: str = "",
    path=None,
) -> dict:
    """Append one meter record. ``hit`` is always null at write time.

    Returns the record plus ``written`` (not stored in the file). An ``OSError``
    on the append is reported as ``written: False`` and does not raise — retrieval
    must not fail because the log could not be appended. A bad path still raises
    ``ValueError`` / ``PermissionError`` from :func:`resolve_path`.
    """
    name = str(route).strip()
    if not name or any(c in name for c in "\r\n"):
        raise ValueError("route must be a single-line name")
    rec = {
        "v": SCHEMA_VERSION,
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "route": name,
        "retrieved_tokens": estimate_tokens(text or ""),
        "cited_slugs": _slugs(cited_slugs),
        "hit": None,
    }
    q = " ".join(str(query).split())[:QUERY_MAX]
    if q:
        rec["query"] = q
    line = json.dumps(rec, ensure_ascii=False, sort_keys=True)
    target = resolve_path(vault_root, path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError:
        rec["written"] = False
        return rec
    rec["written"] = True
    return rec


def _valid(rec) -> bool:
    if not isinstance(rec, dict):
        return False
    if rec.get("v") != SCHEMA_VERSION:
        return False
    if not isinstance(rec.get("route"), str) or not rec["route"]:
        return False
    tokens = rec.get("retrieved_tokens")
    if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 0:
        return False
    slugs = rec.get("cited_slugs")
    if not isinstance(slugs, list) or not all(isinstance(s, str) for s in slugs):
        return False
    if "hit" not in rec or rec["hit"] not in (None, True, False):
        return False
    return True


def read_records(path) -> tuple[list[dict], int]:
    """Return ``(records, skipped)``. A missing file is zero records, not an error."""
    file = pathlib.Path(path)
    if not file.is_file():
        return [], 0
    records: list[dict] = []
    skipped = 0
    for line in file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        if not _valid(rec):
            skipped += 1
            continue
        records.append(rec)
    return records, skipped


def summarize(path) -> dict:
    records, skipped = read_records(path)
    by_route: dict[str, dict] = {}
    cited: dict[str, int] = {}
    hit = miss = pending = tokens = 0
    for rec in records:
        tokens += rec["retrieved_tokens"]
        slot = by_route.setdefault(rec["route"], {"records": 0, "retrieved_tokens": 0})
        slot["records"] += 1
        slot["retrieved_tokens"] += rec["retrieved_tokens"]
        if rec["hit"] is True:
            hit += 1
        elif rec["hit"] is False:
            miss += 1
        else:
            pending += 1
        for slug in rec["cited_slugs"]:
            cited[slug] = cited.get(slug, 0) + 1
    return {
        "records": len(records),
        "retrieved_tokens": tokens,
        "hit": hit,
        "miss": miss,
        "pending": pending,
        "skipped": skipped,
        "by_route": {k: by_route[k] for k in sorted(by_route)},
        "cited_slugs": dict(sorted(cited.items(), key=lambda kv: (-kv[1], kv[0]))),
    }


def line_count(path) -> int:
    """Non-blank lines in the meter file. A missing file is 0."""
    file = pathlib.Path(path)
    if not file.is_file():
        return 0
    return sum(1 for line in file.read_text(encoding="utf-8").splitlines() if line.strip())


def annotate_hits(path, start: int, hit: bool) -> int:
    """Set ``hit`` on records from non-blank line ``start`` onward.

    Records that already have true or false are left alone. This is the local
    write an eval uses after scoring. No network. Returns how many lines changed.
    """
    if hit is not True and hit is not False:
        raise ValueError("hit must be true or false")
    file = pathlib.Path(path)
    if not file.is_file() or start < 0:
        return 0
    lines = file.read_text(encoding="utf-8").splitlines()
    updated = 0
    seen = 0
    out = []
    for line in lines:
        if not line.strip():
            out.append(line)
            continue
        if seen >= start:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                rec = None
            if isinstance(rec, dict) and rec.get("hit") is None:
                rec["hit"] = True if hit else False
                line = json.dumps(rec, ensure_ascii=False, sort_keys=True)
                updated += 1
        out.append(line)
        seen += 1
    file.write_text("\n".join(out) + ("\n" if out else ""), encoding="utf-8")
    return updated


def format_summary(summary: dict) -> str:
    lines = [
        f"records: {summary['records']}",
        f"retrieved_tokens: {summary['retrieved_tokens']}",
        f"hit: {summary['hit']}",
        f"miss: {summary['miss']}",
        f"pending: {summary['pending']}",
        f"skipped: {summary['skipped']}",
        "by_route:",
    ]
    if not summary["by_route"]:
        lines.append("  (none)")
    for route, slot in summary["by_route"].items():
        lines.append(
            f"  {route}\trecords={slot['records']}\ttokens={slot['retrieved_tokens']}"
        )
    lines.append("cited_slugs:")
    if not summary["cited_slugs"]:
        lines.append("  (none)")
    for slug, count in summary["cited_slugs"].items():
        lines.append(f"  {slug}\t{count}")
    return "\n".join(lines)
