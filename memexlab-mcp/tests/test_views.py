import pytest

from memexlab_mcp import views
from memexlab_mcp.vault import Vault


def test_list_views_finds_valid_views(view_vault):
    got = views.list_views(Vault(view_vault))
    assert [v["name"] for v in got] == ["memory-notes"]


def test_members_filters_by_tags_and_excludes_views_dir(view_vault):
    got = views.members(Vault(view_vault), "memory-notes")
    assert [str(p) for p in got] == ["concepts/governed-memory.md"]


def test_members_deterministic(view_vault):
    v = Vault(view_vault)
    assert views.members(v, "memory-notes") == views.members(v, "memory-notes")


def test_unknown_view_and_non_view_note_are_errors(view_vault):
    v = Vault(view_vault)
    with pytest.raises(ValueError, match="no view named"):
        views.load_view(v, "missing")
    with pytest.raises(ValueError, match="not a view"):
        views.load_view(v, "not-a-view")


def test_unknown_query_field_is_error(view_vault):
    (view_vault / "views" / "bad.md").write_text(
        "---\ntype: view\nquery:\n  colour: [red]\n---\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="unknown query fields: colour"):
        views.load_view(Vault(view_vault), "bad")
    # and list_views skips it rather than failing the whole listing
    assert [v["name"] for v in views.list_views(Vault(view_vault))] == ["memory-notes"]


def test_date_bounds(view_vault):
    (view_vault / "views" / "recent.md").write_text(
        "---\ntype: view\nquery:\n  since: 2026-01-01\n---\n", encoding="utf-8"
    )
    got = views.members(Vault(view_vault), "recent")
    # only the dated note on/after 2026-01-01 qualifies; undated notes are excluded
    assert [str(p) for p in got] == ["sources/as-we-may-think.md"]


def test_view_name_cannot_escape_views_dir(view_vault):
    with pytest.raises(ValueError, match="no view named"):
        views.load_view(Vault(view_vault), "../concepts/governed-memory")


def test_server_search_scopes_to_view(view_vault):
    from memexlab_mcp import server

    server.configure(str(view_vault))
    assert server.vault_info()["views"] == ["memory-notes"]
    # empty query falls back to the view's own text field
    hits = server.search_vault(view="memory-notes")
    assert [h["slug"] for h in hits] == ["governed-memory"]
    # explicit query still restricted to view members
    assert server.search_vault("harness", view="memory-notes") == []
    with pytest.raises(ValueError, match="no view named"):
        server.search_vault(view="missing")
