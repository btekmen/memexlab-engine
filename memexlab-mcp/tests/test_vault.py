import pytest
from memexlab_mcp.vault import Vault, parse_frontmatter


def test_vault_rejects_missing_root(tmp_path):
    with pytest.raises(ValueError):
        Vault(tmp_path / "nope")


def test_notes_lists_md_sorted_relative(fixture_vault):
    v = Vault(fixture_vault)
    rels = [str(p) for p in v.notes()]
    assert rels == [
        "concepts/governed-memory.md",
        "concepts/harness-engineering.md",
        "sources/as-we-may-think.md",
    ]


def test_read_by_relative_path_and_slug(fixture_vault):
    v = Vault(fixture_vault)
    by_path = v.read("concepts/governed-memory.md")
    by_slug = v.read("Governed-Memory")
    assert by_path["path"] == by_slug["path"] == "concepts/governed-memory.md"
    assert by_path["frontmatter"]["title"] == "Governed Memory"
    assert "durable, citable" in by_path["body"]


def test_read_unknown_raises(fixture_vault):
    with pytest.raises(FileNotFoundError):
        Vault(fixture_vault).read("does-not-exist")


def test_read_oversize_raises(fixture_vault):
    big = fixture_vault / "concepts" / "big.md"
    big.write_text("x" * 2_000_001, encoding="utf-8")
    with pytest.raises(ValueError):
        Vault(fixture_vault).read("big")


def test_parse_frontmatter_absent_returns_empty_meta():
    meta, body = parse_frontmatter("just text\n")
    assert meta == {} and body == "just text\n"
