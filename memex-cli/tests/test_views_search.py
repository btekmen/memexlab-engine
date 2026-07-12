import json
import pathlib

import pytest

from memex_cli import views as views_mod
from memex_cli.search import search
from memex_cli.vault import Vault


@pytest.fixture
def vault(tmp_path: pathlib.Path) -> Vault:
    (tmp_path / "governance.yml").write_text("write_dir: inbox\n", encoding="utf-8")
    (tmp_path / "concepts").mkdir()
    (tmp_path / "concepts" / "governed-memory.md").write_text(
        "---\ntitle: Governed Memory\ntags: [memory]\nstatus: evergreen\n---\n"
        "Governed memory keeps agent knowledge durable, citable and auditable.\n",
        encoding="utf-8",
    )
    (tmp_path / "concepts" / "platform-banking.md").write_text(
        "---\ntitle: Platform Banking\ntags: [banking]\nstatus: draft\n---\n"
        "Banks as platforms, not pipes.\n",
        encoding="utf-8",
    )
    (tmp_path / "views").mkdir()
    (tmp_path / "views" / "memory-notes.md").write_text(
        "---\ntype: view\ntitle: Memory Notes\nquery:\n  tags: [memory]\n---\n",
        encoding="utf-8",
    )
    return Vault(tmp_path)


def test_views_semantics_match_mcp(vault):
    assert [v["name"] for v in views_mod.list_views(vault)] == ["memory-notes"]
    members = views_mod.members(vault, "memory-notes")
    assert [str(m) for m in members] == ["concepts/governed-memory.md"]
    with pytest.raises(ValueError, match="no view named"):
        views_mod.members(vault, "missing")
    with pytest.raises(ValueError, match="unknown query fields"):
        (vault.root / "views" / "bad.md").write_text(
            "---\ntype: view\nquery:\n  colour: [red]\n---\n", encoding="utf-8")
        views_mod.load_view(vault, "bad")


def test_search_is_deterministic_and_scopable(vault):
    hits = search(vault, "governed citable memory")
    assert hits and hits[0]["slug"] == "governed-memory"
    assert search(vault, "governed") == search(vault, "governed")
    scoped = search(vault, "platforms",
                    allowed={"concepts/governed-memory.md"})
    assert scoped == []


def test_cli_view_and_search(vault, capsys):
    from memex_cli import cli

    code = cli.main(["view", "--vault", str(vault.root)])
    out, _ = capsys.readouterr()
    assert code == 0 and "memory-notes" in out

    code = cli.main(["view", "memory-notes", "--vault", str(vault.root), "--format", "json"])
    out, err = capsys.readouterr()
    payload = json.loads(out)
    assert code == 0 and payload["members"] == ["concepts/governed-memory.md"]
    event = json.loads(err.strip().splitlines()[-1])
    assert event["cmd"] == "view" and event["ok"]

    code = cli.main(["search", "platforms", "--vault", str(vault.root)])
    out, _ = capsys.readouterr()
    assert code == 0 and "[[platform-banking]]" in out

    code = cli.main(["search", "platforms", "--vault", str(vault.root),
                     "--view", "memory-notes"])
    out, _ = capsys.readouterr()
    assert code == 0 and "no hits" in out

    code = cli.main(["view", "missing", "--vault", str(vault.root)])
    assert code == 1
