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
