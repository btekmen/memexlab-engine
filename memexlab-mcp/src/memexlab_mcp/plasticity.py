"""Open local plasticity scores. Read-only. No network.

Keep this module identical to ``memexlab_mcp.plasticity``.

Two policies, both a weighted mean of factors in ``[0, 1]``:

    score = sum(weight * value) / sum(weight)   for weights > 0

``rps`` ranks notes for re-entry (a morning brief). ``mws`` ranks inbox notes
for a human promotion review. Neither policy edits, moves, or uploads a note.

Defaults live in code and match ``schemas/plasticity.defaults.yml``. A vault
overrides them with ``plasticity.yml`` at the vault root. Weights are round
numbers chosen to be auditable, not fitted to an eval set.
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path

import yaml

from .meter import read_records, resolve_path

POLICY_FILE = "plasticity.yml"
_LINK = re.compile(r"\[\[([^\[\]|#]+)")

# Round defaults. Do not fit these to LoCoMo, Tekmen-eval, or the sample vault.
DEFAULTS = {
    "version": 1,
    "rps": {
        "threshold": 0.5,
        "limit": 20,
        "recency_horizon_days": 30,
        "link_cap": 5,
        "meter_hit_cap": 3,
        "weights": {
            "recency": 1,
            "contested": 1,
            "unresolved": 1,
            "links": 1,
            "meter_hits": 1,
        },
    },
    "mws": {
        "threshold": 0.5,
        "limit": 20,
        "substance_chars": 400,
        "link_cap": 3,
        "weights": {
            "substance": 1,
            "provenance": 1,
            "links": 1,
            "not_contested": 1,
            "not_proposal": 1,
        },
    },
}

FORMULA = "sum(weight * value) / sum(weight) for weights > 0"
_INT_KEYS = {
    "version", "limit", "recency_horizon_days", "link_cap", "meter_hit_cap",
    "substance_chars",
}
_FLOAT_KEYS = {"threshold"}


def _write_dir(root: Path) -> str:
    gov = root / "governance.yml"
    if gov.is_file():
        try:
            data = yaml.safe_load(gov.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            data = {}
        if isinstance(data, dict):
            wd = data.get("write_dir")
            if isinstance(wd, str) and wd.strip():
                return wd.strip().strip("/")
    return "inbox"


def _number(key: str, value, *, integer: bool):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number")
    if integer and int(value) != value:
        raise ValueError(f"{key} must be an integer")
    number = int(value) if integer else float(value)
    if key == "version" and number != 1:
        raise ValueError("plasticity version must be 1")
    if key == "threshold" and not 0 <= number <= 1:
        raise ValueError("threshold must be from 0 to 1")
    if key.split(".")[-1] in {"limit", "recency_horizon_days", "link_cap", "meter_hit_cap", "substance_chars"}:
        if number < 1:
            raise ValueError(f"{key} must be >= 1")
    if ".weights." in key and number < 0:
        raise ValueError(f"{key} must be >= 0")
    return number


def _merge(base, override, path: str):
    if not isinstance(override, dict):
        raise ValueError(f"{path or 'plasticity'} must be a mapping")
    out = dict(base)
    for key, value in override.items():
        full = f"{path}.{key}" if path else str(key)
        if key not in base:
            raise ValueError(f"unknown plasticity key: {full}")
        if isinstance(base[key], dict):
            out[key] = _merge(base[key], value, full)
        elif path.endswith("weights"):
            out[key] = _number(full, value, integer=False)
        elif key in _INT_KEYS:
            out[key] = _number(full, value, integer=True)
        elif key in _FLOAT_KEYS:
            out[key] = _number(full, value, integer=False)
        else:
            raise ValueError(f"unknown plasticity key: {full}")
    return out


def load_policy(vault_root) -> tuple[dict, str]:
    """Return ``(policy, source)``. ``source`` is ``defaults`` or ``vault``."""
    root = Path(vault_root)
    path = root / POLICY_FILE
    if not path.is_file():
        return DEFAULTS, "defaults"
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"plasticity.yml is not valid YAML: {exc}") from exc
    if raw is None:
        return DEFAULTS, "defaults"
    if not isinstance(raw, dict):
        raise ValueError("plasticity.yml must be a mapping")
    return _merge(DEFAULTS, raw, ""), "vault"


def _links(body: str) -> list[str]:
    found = []
    for match in _LINK.finditer(body or ""):
        slug = match.group(1).strip()
        if slug:
            found.append(slug)
    return found


def _parse_time(value, fallback: datetime.datetime) -> datetime.datetime:
    if isinstance(value, datetime.datetime):
        stamp = value
    elif isinstance(value, str) and value.strip():
        try:
            stamp = datetime.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return fallback
    else:
        return fallback
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=datetime.timezone.utc)
    return stamp.astimezone(datetime.timezone.utc)


def _age_days(fm: dict, mtime: float, now: datetime.datetime) -> tuple[float, str]:
    file_time = datetime.datetime.fromtimestamp(mtime, datetime.timezone.utc)
    stamp = _parse_time(fm.get("captured_at"), file_time)
    used = "captured_at" if fm.get("captured_at") else "file mtime"
    delta = (now - stamp).total_seconds() / 86400
    if delta < 0:
        return 0.0, f"{used} is in the future; age treated as 0 days"
    return delta, f"age {delta:.4f} days from {used}"


def _status(fm: dict) -> str:
    value = fm.get("status")
    if value is None or isinstance(value, (list, dict)):
        return ""
    return str(value).strip().casefold()


def _resolution(fm: dict) -> str:
    value = fm.get("resolution")
    if not isinstance(value, str):
        return ""
    return value.strip().casefold()


def _factor(name: str, weight: float, value: float, detail: str) -> dict:
    return {
        "factor": name,
        "weight": weight,
        "value": round(value, 6),
        "contribution": round(weight * value, 6),
        "detail": detail,
    }


def _score(factors: list[dict]) -> float:
    total_w = sum(f["weight"] for f in factors if f["weight"] > 0)
    if total_w <= 0:
        return 0.0
    return round(sum(f["contribution"] for f in factors if f["weight"] > 0) / total_w, 6)


def _meter_hit_counts(vault_root) -> dict[str, int]:
    try:
        path = resolve_path(vault_root)
    except (OSError, ValueError, PermissionError):
        return {}
    records, _skipped = read_records(path)
    counts: dict[str, int] = {}
    for rec in records:
        if rec.get("hit") is not True:
            continue
        for slug in rec["cited_slugs"]:
            counts[slug] = counts.get(slug, 0) + 1
    return counts


def _open_loop(fm: dict) -> tuple[bool, str]:
    status = _status(fm)
    if status == "contested":
        return True, "status is contested"
    if _resolution(fm) == "proposed":
        return True, "resolution is proposed and not applied"
    if str(fm.get("type") or "").strip().casefold() == "queue-item" and status == "pending":
        return True, "queue item is pending"
    return False, ""


def _rps_factors(note: dict, mtime: float, now: datetime.datetime, policy: dict,
                 hits: dict[str, int]) -> list[dict]:
    fm = note["frontmatter"] if isinstance(note.get("frontmatter"), dict) else {}
    weights = policy["weights"]
    age, age_detail = _age_days(fm, mtime, now)
    horizon = policy["recency_horizon_days"]
    recency = min(1.0, age / horizon)
    status = _status(fm)
    contested = 1.0 if status == "contested" else 0.0
    resolution = _resolution(fm)
    unresolved = 1.0 if resolution == "proposed" else 0.0
    n_links = len(_links(note.get("body") or ""))
    links = min(1.0, n_links / policy["link_cap"])
    slug = Path(note["path"]).stem
    n_hits = hits.get(slug, 0)
    meter = min(1.0, n_hits / policy["meter_hit_cap"])
    return [
        _factor("recency", weights["recency"], recency,
                f"{age_detail}; value = min(1, age / {horizon} days)"),
        _factor("contested", weights["contested"], contested,
                "status is contested" if contested else f"status is {status or 'absent'}"),
        _factor("unresolved", weights["unresolved"], unresolved,
                "resolution is proposed" if unresolved else "no proposed resolution on this note"),
        _factor("links", weights["links"], links,
                f"{n_links} wikilinks / cap {policy['link_cap']}"),
        _factor("meter_hits", weights["meter_hits"], meter,
                f"{n_hits} meter records with hit true cite this slug / cap {policy['meter_hit_cap']}"),
    ]


def _mws_factors(note: dict, policy: dict, known: set[str]) -> list[dict]:
    fm = note["frontmatter"] if isinstance(note.get("frontmatter"), dict) else {}
    weights = policy["weights"]
    body = (note.get("body") or "").strip()
    substance = min(1.0, len(body) / policy["substance_chars"])
    sources = fm.get("sources")
    origin = fm.get("origin_ref")
    has_sources = isinstance(sources, list) and any(str(s).strip() for s in sources)
    has_origin = isinstance(origin, str) and bool(origin.strip())
    provenance = 1.0 if has_sources or has_origin else 0.0
    own = Path(note["path"]).stem.casefold()
    resolved = [s for s in _links(note.get("body") or "")
                if s.casefold() in known and s.casefold() != own]
    links = min(1.0, len(resolved) / policy["link_cap"])
    contested = _status(fm) == "contested"
    proposal = _resolution(fm) == "proposed"
    if has_sources and has_origin:
        provenance_detail = "sources and origin_ref are set"
    elif has_sources:
        provenance_detail = "sources is set"
    elif has_origin:
        provenance_detail = "origin_ref is set"
    else:
        provenance_detail = "no sources and no origin_ref"
    return [
        _factor("substance", weights["substance"], substance,
                f"{len(body)} body characters / {policy['substance_chars']}"),
        _factor("provenance", weights["provenance"], provenance, provenance_detail),
        _factor("links", weights["links"], links,
                f"{len(resolved)} wikilinks resolve to another note / cap {policy['link_cap']}"),
        _factor("not_contested", weights["not_contested"], 0.0 if contested else 1.0,
                "status is contested, so this is a conflict note"
                if contested else "status is not contested"),
        _factor("not_proposal", weights["not_proposal"], 0.0 if proposal else 1.0,
                "resolution is proposed, so this waits on a human"
                if proposal else "this note is not a resolution proposal"),
    ]


def _row(note: dict, factors: list[dict], policy: dict) -> dict:
    fm = note["frontmatter"] if isinstance(note.get("frontmatter"), dict) else {}
    score = _score(factors)
    loop, reason = _open_loop(fm)
    return {
        "slug": Path(note["path"]).stem,
        "path": note["path"],
        "title": "" if fm.get("title") is None else str(fm.get("title")),
        "score": score,
        "threshold": policy["threshold"],
        "recommend": score >= policy["threshold"],
        "open_loop": loop,
        "open_loop_reason": reason,
        "factors": factors,
    }


def score_plasticity(vault, policy: str = "all", *, limit: int | None = None,
                     now: datetime.datetime | None = None) -> dict:
    """Score ``rps``, ``mws``, or ``all``. Reads the vault. Writes nothing."""
    if policy not in {"rps", "mws", "all"}:
        raise ValueError("policy must be rps, mws, or all")
    if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 1):
        raise ValueError("limit must be an integer >= 1")
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=datetime.timezone.utc)
    loaded, source = load_policy(vault.root)
    names = ["rps", "mws"] if policy == "all" else [policy]
    hits = _meter_hit_counts(vault.root)
    known = set()
    notes = []
    for rel in vault.notes():
        try:
            note = vault.read(str(rel))
        except (ValueError, OSError, FileNotFoundError):
            continue
        full = vault.root / rel
        try:
            mtime = full.stat().st_mtime
        except OSError:
            continue
        notes.append((rel, note, mtime))
        known.add(rel.stem.casefold())
    inbox = _write_dir(vault.root)
    reports = {}
    for name in names:
        block = loaded[name]
        cap = limit if limit is not None else block["limit"]
        rows = []
        for rel, note, mtime in notes:
            if name == "mws" and (not rel.parts or rel.parts[0] != inbox):
                continue
            if name == "rps":
                factors = _rps_factors(note, mtime, now, block, hits)
            else:
                factors = _mws_factors(note, block, known)
            rows.append(_row(note, factors, block))
        rows.sort(key=lambda row: (-row["score"], row["path"]))
        reports[name] = {
            "policy": name,
            "purpose": (
                "Which notes should re-enter a morning brief."
                if name == "rps"
                else "Which inbox notes a human might promote. Recommendation only."
            ),
            "formula": FORMULA,
            "weights_from": source,
            "threshold": block["threshold"],
            "weights": block["weights"],
            "scored": len(rows),
            "shown": min(cap, len(rows)),
            "notes": rows[:cap],
        }
    return {
        "cmd": "plasticity",
        "read_only": True,
        "edited": False,
        "moved": False,
        "network": False,
        "weights_from": source,
        "policy_file": str(vault.root / POLICY_FILE) if source == "vault" else None,
        "now": now.astimezone(datetime.timezone.utc).isoformat(),
        "policies": reports,
    }


def format_report(report: dict) -> str:
    lines = [
        f"plasticity  weights: {report['weights_from']}  read-only",
        f"formula: {FORMULA}",
    ]
    for name, block in report["policies"].items():
        lines.append(f"\n{name}  {block['purpose']}  threshold {block['threshold']}")
        if not block["notes"]:
            lines.append("  (no notes)")
            continue
        for row in block["notes"]:
            mark = "recommend" if row["recommend"] else "below threshold"
            lines.append(f"[[{row['slug']}]]\t{row['score']}\t{mark}\t{row['path']}")
            for factor in row["factors"]:
                lines.append(
                    f"  {factor['factor']}: weight {factor['weight']} "
                    f"value {factor['value']} contribution {factor['contribution']} "
                    f"— {factor['detail']}"
                )
    return "\n".join(lines) + "\n"
