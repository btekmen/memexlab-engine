from memexlab_mcp.search import search
from memexlab_mcp.vault import Vault


def test_relevance_orders_matching_note_first(fixture_vault):
    hits = search(Vault(fixture_vault), "governed citable memory")
    assert hits and hits[0]["slug"] == "governed-memory"
    assert hits[0]["path"] == "concepts/governed-memory.md"
    assert "citable" in hits[0]["snippet"]


def test_determinism_identical_runs(fixture_vault):
    v = Vault(fixture_vault)
    assert search(v, "memex trails") == search(v, "memex trails")


def test_empty_and_miss_queries_return_empty(fixture_vault):
    v = Vault(fixture_vault)
    assert search(v, "") == []
    assert search(v, "zzzunknowntoken") == []


def test_limit_respected(fixture_vault):
    assert len(search(Vault(fixture_vault), "the memory harness", limit=1)) == 1


def test_search_skips_unreadable_notes(fixture_vault):
    big = fixture_vault / "concepts" / "huge.md"
    big.write_text("x" * 2_000_001, encoding="utf-8")
    hits = search(Vault(fixture_vault), "governed citable memory")
    assert hits and hits[0]["slug"] == "governed-memory"
    assert all(h["slug"] != "huge" for h in hits)
