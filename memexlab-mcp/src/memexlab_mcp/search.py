"""Deterministic BM25 search — no embeddings, stable ordering."""
from __future__ import annotations

import math
import re

from .vault import Vault

K1, B = 1.5, 0.75
_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.casefold())


def search(vault: Vault, query: str, limit: int = 5, allowed: set[str] | None = None) -> list[dict]:
    """BM25 over the vault; `allowed` (relative-path strings) restricts the corpus."""
    q = _tokens(query)
    if not q:
        return []
    docs = []
    for rel in vault.notes():
        if allowed is not None and str(rel) not in allowed:
            continue
        try:
            note = vault.read(str(rel))
        except (ValueError, OSError, FileNotFoundError):
            continue
        title = str(note["frontmatter"].get("title", ""))
        toks = _tokens(f"{rel.stem} {title} {note['body']}")
        docs.append((rel, note["body"], toks))
    if not docs:
        return []
    n = len(docs)
    avgdl = sum(len(t) for *_, t in docs) / n
    df: dict[str, int] = {}
    for term in set(q):
        df[term] = sum(1 for *_, t in docs if term in t)
    out = []
    for rel, body, toks in docs:
        dl = len(toks) or 1
        score = 0.0
        for term in q:
            tf = toks.count(term)
            if tf == 0 or df[term] == 0:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * (tf * (K1 + 1)) / (tf + K1 * (1 - B + B * dl / avgdl))
        if score > 0:
            first = next((t for t in q if t in body.casefold()), q[0])
            i = body.casefold().find(first)
            snippet = body[max(0, i - 40) : i + 80].strip().replace("\n", " ") if i >= 0 else body[:80].strip()
            out.append({"slug": rel.stem, "path": str(rel), "score": round(score, 6), "snippet": snippet})
    out.sort(key=lambda h: (-h["score"], h["path"]))
    return out[:limit]
