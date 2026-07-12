import pathlib
import pytest


@pytest.fixture
def fixture_vault(tmp_path: pathlib.Path) -> pathlib.Path:
    (tmp_path / "concepts").mkdir()
    (tmp_path / "sources").mkdir()
    (tmp_path / "concepts" / "governed-memory.md").write_text(
        "---\ntitle: Governed Memory\ntags: [memory]\n---\n"
        "Governed memory keeps agent knowledge durable, citable and auditable.\n",
        encoding="utf-8",
    )
    (tmp_path / "concepts" / "harness-engineering.md").write_text(
        "Harness engineering: reliability comes from the harness, not the prompt.\n",
        encoding="utf-8",
    )
    (tmp_path / "sources" / "as-we-may-think.md").write_text(
        "---\ntitle: As We May Think\n---\nBush imagined the memex with associative trails.\n",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def view_vault(fixture_vault: pathlib.Path) -> pathlib.Path:
    """fixture_vault plus a views/ dir, a dated note, and a non-view note in views/."""
    (fixture_vault / "sources" / "as-we-may-think.md").write_text(
        "---\ntitle: As We May Think\ndate: 2026-03-01\n---\n"
        "Bush imagined the memex with associative trails.\n",
        encoding="utf-8",
    )
    (fixture_vault / "views").mkdir()
    (fixture_vault / "views" / "memory-notes.md").write_text(
        "---\ntype: view\ntitle: Memory Notes\nquery:\n  tags: [memory]\n  text: governed\n---\n"
        "Notes tagged memory.\n",
        encoding="utf-8",
    )
    (fixture_vault / "views" / "not-a-view.md").write_text(
        "---\ntitle: Stray Note\n---\nnot a view\n", encoding="utf-8"
    )
    return fixture_vault
