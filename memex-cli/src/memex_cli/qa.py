"""`memex qa` — one question, one cited answer. The citation contract is
checked, not hoped: every [[slug]] in the answer must resolve to a note that was
actually in the model's context, and the numbers go into the JSON event.

Retrieval is the same deterministic BM25 as `memex search`; `--view` scopes it.
Output goes to stdout by default; `--apply` files it into the qa dir (default
`_qa/`, `qa_dir:` in the vault's governance.yml overrides).
"""
from __future__ import annotations

import datetime
import importlib.resources
import pathlib
import re

import yaml

from . import llm
from .search import search
from .vault import Vault
from .views import members as view_members

NOTE_CHAR_CAP = 4000
DEFAULT_K = 6
LENSES = ("keypoints", "eli5", "translate", "counter", "actions")
_CITE = re.compile(r"\[\[([^\]#|]+)")

SYSTEM = """You answer questions from a personal knowledge vault.

Rules, non-negotiable:
- Use ONLY the notes provided below as sources.
- Cite every claim with the note's [[slug]] inline. A paragraph without a
  citation is a defect.
- If the notes do not answer the question, say exactly what is missing —
  never fill gaps from general knowledge.
{lens}
Notes:
{context}"""


def load_lens(vault: Vault, name: str | None, lang: str | None) -> str:
    if not name:
        return ""
    if name not in LENSES:
        raise ValueError(f"unknown lens '{name}' (available: {', '.join(LENSES)})")
    override = vault.root / "lenses" / f"{name}.md"
    if override.is_file():
        text = override.read_text(encoding="utf-8")
    else:
        text = (importlib.resources.files("memex_cli") / "lenses" / f"{name}.md").read_text(encoding="utf-8")
    if name == "translate":
        if not lang:
            raise ValueError("the translate lens needs --lang (e.g. --lang tr)")
        text = text.replace("{lang}", lang)
    return "\nLens for this answer:\n" + text.strip() + "\n"


def _qa_dir(vault: Vault) -> str:
    gov = vault.root / "governance.yml"
    if gov.is_file():
        try:
            data = yaml.safe_load(gov.read_text(encoding="utf-8")) or {}
            qd = data.get("qa_dir") if isinstance(data, dict) else None
            if isinstance(qd, str) and qd.strip():
                return qd.strip()
        except yaml.YAMLError:
            pass
    return "_qa"


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")
    return slug[:60].rstrip("-") or "question"


def citation_lint(answer: str, context_slugs: set[str]) -> dict:
    cited = [c.strip() for c in _CITE.findall(answer)]
    valid = [c for c in cited if c in context_slugs]
    paragraphs = [p for p in answer.split("\n\n") if len(p.strip()) > 80]
    uncited = sum(1 for p in paragraphs if "[[" not in p)
    return {"citations_total": len(cited), "citations_valid": len(valid),
            "citations_invalid": sorted(set(cited) - context_slugs),
            "uncited_paragraphs": uncited}


def qa(
    vault: Vault, question: str, lens: str | None = None, lang: str | None = None,
    view: str | None = None, include: list[str] | None = None,
    k: int = DEFAULT_K, max_tokens: int = 1000, apply: bool = False,
    strict: bool = False,
    provider: dict | None = None, complete=None,
) -> dict:
    """`provider`/`complete` are injectable for tests — no network, no keys."""
    allowed = None
    if view:
        allowed = {str(m) for m in view_members(vault, view)}
    hits = search(vault, question, limit=k, allowed=allowed)
    paths = [h["path"] for h in hits]
    for slug in include or []:
        for rel in vault.notes():
            if rel.stem == slug and str(rel) not in paths:
                paths.append(str(rel))

    context_blocks, slugs = [], set()
    for path in paths:
        note = vault.read(path)
        slug = pathlib.Path(path).stem
        slugs.add(slug)
        context_blocks.append(f"[[{slug}]]\n{note['body'][:NOTE_CHAR_CAP].strip()}")
    if not context_blocks:
        return {"action": "no-context", "question": question, "ok": False,
                "hint": "retrieval found nothing — try other terms, --view, or --include"}

    prov = provider or llm.resolve_provider()
    complete = complete or llm.complete
    system = SYSTEM.format(lens=load_lens(vault, lens, lang),
                           context="\n\n---\n\n".join(context_blocks))
    reply = complete(prov, system, question, max_tokens=max_tokens)
    lint = citation_lint(reply["text"], slugs)

    result = {"action": "qa", "question": question, "answer": reply["text"],
              "model": reply["model"], "route": prov["route"], "lens": lens,
              "context_slugs": sorted(slugs), "usage": reply["usage"],
              **lint, "applied": False,
              "ok": not (strict and (lint["citations_invalid"] or lint["citations_total"] == 0))}

    if apply and result["ok"]:
        now = datetime.datetime.now(datetime.timezone.utc)
        qd = _qa_dir(vault)
        target_dir = (vault.root / qd).resolve()
        if not target_dir.is_relative_to(vault.root):
            raise PermissionError(f"qa dir escapes vault: {qd}")
        target_dir.mkdir(parents=True, exist_ok=True)
        rel = pathlib.Path(qd) / f"{now.strftime('%Y%m%d-%H%M%S')}-{_slugify(question)}.md"
        frontmatter = {"title": question, "type": "qa", "status": "draft",
                       "created": now.isoformat(), "model": reply["model"],
                       "lens": lens or "none",
                       "cited_slugs": sorted(set(c for c in _CITE.findall(reply["text"])
                                                 if c.strip() in slugs))}
        (vault.root / rel).write_text(
            "---\n" + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)
            + "---\n\n# " + question + "\n\n" + reply["text"].strip() + "\n",
            encoding="utf-8")
        result["note"] = str(rel)
        result["applied"] = True
    return result
