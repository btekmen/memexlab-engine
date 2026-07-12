import hashlib
import json
import pathlib

import pytest

from memex_cli import index as index_mod
from memex_cli.index import (hybrid_rank, index_status, load_index, reindex,
                             resolve_embedder)
from memex_cli.search import search
from memex_cli.vault import Vault

EMBEDDER = {"url": "http://local", "key": "", "model": "fake-embed", "route": "local"}


def fake_embed(embedder, texts):
    """Deterministic toy embedder: 8-dim vectors from token hashes."""
    out = []
    for t in texts:
        vec = [0.0] * 8
        for tok in t.casefold().split():
            vec[int(hashlib.sha256(tok.encode()).hexdigest(), 16) % 8] += 1.0
        out.append(vec)
    return out


@pytest.fixture
def vault(tmp_path: pathlib.Path) -> Vault:
    (tmp_path / "governance.yml").write_text("write_dir: inbox\n", encoding="utf-8")
    (tmp_path / "concepts").mkdir()
    (tmp_path / "concepts" / "governed-memory.md").write_text(
        "---\ntitle: Governed Memory\n---\n"
        "durable citable auditable memory boundary\n", encoding="utf-8")
    (tmp_path / "concepts" / "platform-banking.md").write_text(
        "---\ntitle: Platform Banking\n---\n"
        "banks platforms pipes embedded finance\n", encoding="utf-8")
    return Vault(tmp_path)


def test_embedder_resolution_order_and_refusal():
    e = resolve_embedder({"MEMEX_EMBED_URL": "http://x/v1", "GLM_API_KEY": "g"})
    assert e["route"] == "local"
    e = resolve_embedder({"GLM_API_KEY": "g"})
    assert e["route"] == "glm" and e["model"] == "embedding-3"
    e = resolve_embedder({"OPENAI_API_KEY": "o", "MEMEX_EMBED_MODEL": "custom"})
    assert e["route"] == "openai" and e["model"] == "custom"
    with pytest.raises(RuntimeError, match="keyword search never"):
        resolve_embedder({})


def test_reindex_dry_run_writes_nothing(vault):
    res = reindex(vault, apply=False)
    assert res["to_embed"] == 2 and not res["applied"]
    assert not (vault.root / ".memex" / "embeddings").exists()


def test_reindex_apply_then_current_and_incremental(vault):
    res = reindex(vault, apply=True, embedder=EMBEDDER, embed=fake_embed)
    assert res["embedded"] == 2 and res["current"]
    status = index_status(vault)
    assert status["current"] and status["fresh"] == 2
    # touch one note -> exactly one stale
    (vault.root / "concepts" / "governed-memory.md").write_text(
        "---\ntitle: Governed Memory\n---\nchanged body entirely\n", encoding="utf-8")
    status = index_status(vault)
    assert status["stale"] == 1 and not status["current"]
    res = reindex(vault, apply=True, embedder=EMBEDDER, embed=fake_embed)
    assert res["embedded"] == 1 and res["current"]


def test_index_is_rebuildable_cache(vault):
    reindex(vault, apply=True, embedder=EMBEDDER, embed=fake_embed)
    first = (vault.root / ".memex" / "embeddings" / "vectors.jsonl").read_text()
    import shutil
    shutil.rmtree(vault.root / ".memex" / "embeddings")
    reindex(vault, apply=True, embedder=EMBEDDER, embed=fake_embed)
    second = (vault.root / ".memex" / "embeddings" / "vectors.jsonl").read_text()
    assert first == second  # same vault + same model => identical index


def test_deleted_notes_drop_from_index(vault):
    reindex(vault, apply=True, embedder=EMBEDDER, embed=fake_embed)
    (vault.root / "concepts" / "platform-banking.md").unlink()
    (vault.root / "concepts" / "new-note.md").write_text(
        "---\ntitle: New\n---\nnew content\n", encoding="utf-8")
    res = reindex(vault, apply=True, embedder=EMBEDDER, embed=fake_embed)
    idx = load_index(vault)
    assert "concepts/platform-banking.md" not in idx["vectors"]
    assert "concepts/new-note.md" in idx["vectors"]
    assert res["current"]


def test_hybrid_refuses_on_stale_index(vault):
    with pytest.raises(RuntimeError, match="reindex"):
        hybrid_rank(vault, "memory", [], 5, embedder=EMBEDDER, embed=fake_embed)


def test_hybrid_finds_semantic_match_bm25_misses(vault):
    reindex(vault, apply=True, embedder=EMBEDDER, embed=fake_embed)
    # query shares a token with the note body ('citable') but scores zero in a
    # bm25 corpus? it doesn't — so use a token that only embedding-space sees:
    # fake_embed buckets 'auditable' and query word into same dims via shared tokens
    query = "auditable boundary"
    bm25_hits = search(vault, "zzz-no-keyword-match")
    assert bm25_hits == []
    hits = hybrid_rank(vault, query, bm25_hits, 5, embedder=EMBEDDER, embed=fake_embed)
    assert hits and hits[0]["slug"] == "governed-memory"


def test_cli_reindex_and_hybrid(vault, capsys, monkeypatch):
    from memex_cli import cli

    monkeypatch.setattr(index_mod, "embed_texts", fake_embed)
    monkeypatch.setenv("MEMEX_EMBED_URL", "http://stub")
    code = cli.main(["reindex", "--vault", str(vault.root)])
    out, _ = capsys.readouterr()
    assert code == 0 and "2 note(s) need embedding" in out

    code = cli.main(["reindex", "--vault", str(vault.root), "--verify"])
    assert code == 1  # stale until applied
    capsys.readouterr()

    code = cli.main(["reindex", "--vault", str(vault.root), "--apply"])
    out, _ = capsys.readouterr()
    assert code == 0 and "embedded 2 note(s)" in out

    code = cli.main(["reindex", "--vault", str(vault.root), "--verify"])
    out, _ = capsys.readouterr()
    assert code == 0 and "index is current" in out

    code = cli.main(["search", "auditable boundary", "--vault", str(vault.root),
                     "--mode", "hybrid", "--format", "json"])
    out, _ = capsys.readouterr()
    hits = json.loads(out)
    assert code == 0 and hits[0]["slug"] == "governed-memory"
