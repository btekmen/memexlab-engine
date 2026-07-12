"""The local semantic index — a derived cache, rebuildable from the vault,
never a second source of truth (invariant 1, enforced by design and testable
with `memex reindex --verify`).

Storage: `.memex/embeddings/manifest.json` (model id, dimensions) +
`.memex/embeddings/vectors.jsonl` (one `{path, hash, vec}` per note). Content
hashes invalidate exactly the notes that changed. Delete the directory at any
time — nothing is lost but compute.

Embedding provider (environment only, embeddings never leave the machine on
the local route):
  1. MEMEX_EMBED_URL   any OpenAI-compatible /embeddings endpoint (llama.cpp,
                       Ollama, LM Studio) — the sovereign route
  2. GLM_API_KEY       GLM embeddings (default model embedding-3)
  3. OPENAI_API_KEY    OpenAI (default text-embedding-3-small)
MEMEX_EMBED_MODEL overrides the model id on any route.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import urllib.request

from .vault import Vault

EMB_DIR = pathlib.Path(".memex") / "embeddings"
GLM_EMBED_MODEL = "embedding-3"
OPENAI_EMBED_MODEL = "text-embedding-3-small"
NOTE_CHAR_CAP = 6000
EMBED_REFUSAL = ("reindex/hybrid need an embedding provider; keyword search never "
                 "does. Set MEMEX_EMBED_URL (local endpoint), GLM_API_KEY, or "
                 "OPENAI_API_KEY.")


def resolve_embedder(env: dict | None = None) -> dict:
    e = os.environ if env is None else env
    model = (e.get("MEMEX_EMBED_MODEL") or "").strip()
    if (e.get("MEMEX_EMBED_URL") or "").strip():
        return {"url": e["MEMEX_EMBED_URL"].strip().rstrip("/"), "key": "",
                "model": model or "default", "route": "local"}
    if (e.get("GLM_API_KEY") or "").strip():
        from .llm import GLM_DEFAULT_URL
        return {"url": (e.get("GLM_API_URL") or GLM_DEFAULT_URL).rstrip("/"),
                "key": e["GLM_API_KEY"].strip(),
                "model": model or GLM_EMBED_MODEL, "route": "glm"}
    if (e.get("OPENAI_API_KEY") or "").strip():
        return {"url": "https://api.openai.com/v1", "key": e["OPENAI_API_KEY"].strip(),
                "model": model or OPENAI_EMBED_MODEL, "route": "openai"}
    raise RuntimeError(EMBED_REFUSAL)


def embed_texts(embedder: dict, texts: list[str]) -> list[list[float]]:
    headers = {"Content-Type": "application/json"}
    if embedder["key"]:
        headers["Authorization"] = f"Bearer {embedder['key']}"
    req = urllib.request.Request(
        f"{embedder['url']}/embeddings",
        data=json.dumps({"model": embedder["model"], "input": texts}).encode("utf-8"),
        headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    rows = sorted(data.get("data", []), key=lambda d: d.get("index", 0))
    return [r["embedding"] for r in rows]


def _note_hash(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:24]


def load_index(vault: Vault) -> dict:
    """→ {model, dim, vectors: {path: {hash, vec}}} — empty structure if absent."""
    base = vault.root / EMB_DIR
    out = {"model": "", "dim": 0, "vectors": {}}
    mf = base / "manifest.json"
    vf = base / "vectors.jsonl"
    if mf.is_file():
        try:
            out.update(json.loads(mf.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            pass
    if vf.is_file():
        for line in vf.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
                out["vectors"][row["path"]] = {"hash": row["hash"], "vec": row["vec"]}
            except (json.JSONDecodeError, KeyError):
                continue
    return out


def index_status(vault: Vault) -> dict:
    """Deterministic staleness report — no provider needed."""
    idx = load_index(vault)
    fresh = stale = missing = 0
    extraneous = set(idx["vectors"])
    for rel in vault.notes():
        path = str(rel)
        extraneous.discard(path)
        try:
            body = vault.read(path)["body"]
        except (ValueError, OSError, FileNotFoundError):
            continue
        rec = idx["vectors"].get(path)
        if rec is None:
            missing += 1
        elif rec["hash"] != _note_hash(body):
            stale += 1
        else:
            fresh += 1
    return {"model": idx["model"], "notes": fresh + stale + missing,
            "fresh": fresh, "stale": stale, "missing": missing,
            "orphaned": len(extraneous), "current": stale == 0 and missing == 0}


def reindex(vault: Vault, apply: bool = False, embedder: dict | None = None,
            embed=None, batch: int = 16) -> dict:
    status = index_status(vault)
    todo = []
    idx = load_index(vault)
    for rel in vault.notes():
        path = str(rel)
        try:
            body = vault.read(path)["body"]
        except (ValueError, OSError, FileNotFoundError):
            continue
        h = _note_hash(body)
        rec = idx["vectors"].get(path)
        if rec is None or rec["hash"] != h:
            todo.append((path, h, body[:NOTE_CHAR_CAP]))
    result = {"action": "reindex", "to_embed": len(todo), **status, "applied": apply,
              "ok": True}
    if not apply or not todo:
        return result

    emb = embedder or resolve_embedder()
    embed = embed or embed_texts
    for i in range(0, len(todo), batch):
        chunk = todo[i:i + batch]
        vecs = embed(emb, [b for _, _, b in chunk])
        for (path, h, _), vec in zip(chunk, vecs):
            idx["vectors"][path] = {"hash": h, "vec": vec}
    # drop vectors for deleted notes
    live = {str(r) for r in vault.notes()}
    idx["vectors"] = {p: v for p, v in idx["vectors"].items() if p in live}

    base = vault.root / EMB_DIR
    base.mkdir(parents=True, exist_ok=True)
    dim = len(next(iter(idx["vectors"].values()))["vec"]) if idx["vectors"] else 0
    (base / "manifest.json").write_text(json.dumps(
        {"model": emb["model"], "route": emb["route"], "dim": dim},
        ensure_ascii=False) + "\n", encoding="utf-8")
    with (base / "vectors.jsonl").open("w", encoding="utf-8") as f:
        for path, rec in sorted(idx["vectors"].items()):
            f.write(json.dumps({"path": path, **rec}, ensure_ascii=False) + "\n")
    result.update(index_status(vault))
    result["embedded"] = len(todo)
    result["model"] = emb["model"]
    return result


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


def hybrid_rank(vault: Vault, query: str, bm25_hits: list[dict], limit: int,
                embedder: dict | None = None, embed=None,
                allowed: set[str] | None = None) -> list[dict]:
    """Ensemble: normalized BM25 ∪ cosine over the cached index, 0.5/0.5.

    Requires a CURRENT index (reindex first) — refuses on stale so results stay
    reproducible: same vault + same cached vectors ⇒ same ranking.
    """
    status = index_status(vault)
    if not status["current"]:
        raise RuntimeError(
            f"semantic index is not current ({status['stale']} stale, "
            f"{status['missing']} missing) — run `memex reindex --apply` first")
    idx = load_index(vault)
    emb = embedder or resolve_embedder()
    embed = embed or embed_texts
    qvec = embed(emb, [query])[0]

    sem = {}
    for path, rec in idx["vectors"].items():
        if allowed is not None and path not in allowed:
            continue
        sem[path] = _cosine(qvec, rec["vec"])
    max_bm = max((h["score"] for h in bm25_hits), default=0.0) or 1.0
    bm = {h["path"]: h["score"] / max_bm for h in bm25_hits}
    snippets = {h["path"]: h["snippet"] for h in bm25_hits}

    merged = []
    for path in set(bm) | set(sem):
        score = 0.5 * bm.get(path, 0.0) + 0.5 * max(sem.get(path, 0.0), 0.0)
        merged.append({"slug": pathlib.Path(path).stem, "path": path,
                       "score": round(score, 6),
                       "snippet": snippets.get(path, "")})
    merged.sort(key=lambda h: (-h["score"], h["path"]))
    return merged[:limit]
