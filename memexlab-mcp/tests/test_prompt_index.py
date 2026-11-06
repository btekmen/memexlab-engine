import pytest

from memexlab_mcp.prompt_index import build_prompt_index
from memexlab_mcp.vault import Vault


def test_index_is_compact_and_section_scoped(fixture_vault):
    vault = Vault(fixture_vault)
    idx = build_prompt_index(vault)
    assert idx["truncated"] is False
    assert idx["count"] == 3
    assert "durable, citable and auditable" not in idx["prompt"]
    body_keys = {"body", "frontmatter"}
    assert body_keys.isdisjoint(idx["notes"][0])
    concepts = build_prompt_index(vault, section="concepts")
    assert {n["section"] for n in concepts["notes"]} == {"concepts"}
    assert concepts["count"] == 2
    with pytest.raises(ValueError):
        build_prompt_index(vault, section="../secrets")


def test_index_respects_char_budget(fixture_vault):
    idx = build_prompt_index(Vault(fixture_vault), max_chars=80)
    assert idx["truncated"] is True
    assert idx["count"] < idx["total"]
    assert len(idx["prompt"]) <= 80
