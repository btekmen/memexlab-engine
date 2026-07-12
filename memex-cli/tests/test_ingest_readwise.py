import json
import pathlib

import pytest

from memex_cli.ingest_readwise import ingest_readwise
from memex_cli.vault import Vault

BOOKS = [
    {
        "user_book_id": 101,
        "title": "As We May Think",
        "author": "Vannevar Bush",
        "category": "articles",
        "source_url": "https://example.com/awmt",
        "highlights": [
            {"id": 1, "text": "The human mind operates by association.",
             "location": 12, "highlighted_at": "2026-06-01T10:00:00Z", "note": ""},
            {"id": 2, "text": "Trails that do not fade.",
             "location": 40, "highlighted_at": "2026-06-02T10:00:00Z",
             "note": "Link to governed memory."},
        ],
    },
    {
        "user_book_id": 202,
        "title": "Deep Work",
        "author": "Cal Newport",
        "category": "books",
        "highlights": [
            {"id": 3, "text": "Clarity about what matters.",
             "location": 345, "highlighted_at": "2026-06-03T10:00:00Z", "note": ""},
        ],
    },
]


@pytest.fixture
def vault(tmp_path: pathlib.Path) -> Vault:
    (tmp_path / "governance.yml").write_text("write_dir: inbox\n", encoding="utf-8")
    return Vault(tmp_path)


def test_dry_run_writes_nothing(vault):
    res = ingest_readwise(vault, "tok", apply=False, books=BOOKS)
    assert res["ok"] and res["new_highlights"] == 3 and len(res["plan"]) == 2
    assert res["since"] == "(full export)"
    assert not (vault.root / "inbox").exists()
    assert not (vault.root / ".memex").exists()


def test_apply_creates_notes_with_provenance_and_notes(vault):
    ingest_readwise(vault, "tok", apply=True, books=BOOKS)
    notes = sorted((vault.root / "inbox").glob("*.md"))
    assert len(notes) == 2
    awmt = next(n for n in notes if "as-we-may-think" in n.name).read_text()
    assert "captured_via: readwise" in awmt
    assert "readwise_id: 101" in awmt
    assert "source_url: https://example.com/awmt" in awmt
    assert "> Trails that do not fade." in awmt
    assert "**Note.** Link to governed memory." in awmt


def test_reimport_is_zero_delta_and_cursor_advances(vault):
    ingest_readwise(vault, "tok", apply=True, books=BOOKS)
    state1 = json.loads((vault.root / ".memex" / "ingest_state.json").read_text())
    assert state1["readwise"]["cursor"]
    before = {p.name: p.read_text() for p in (vault.root / "inbox").glob("*.md")}
    res = ingest_readwise(vault, "tok", apply=True, books=BOOKS)
    after = {p.name: p.read_text() for p in (vault.root / "inbox").glob("*.md")}
    assert res["new_highlights"] == 0 and res["known_skipped"] == 3
    assert before == after


def test_new_highlight_appends_and_user_edits_survive(vault):
    ingest_readwise(vault, "tok", apply=True, books=BOOKS)
    deep = next(p for p in (vault.root / "inbox").glob("*.md") if "deep-work" in p.name)
    deep.write_text(deep.read_text() + "\nMY OWN THOUGHTS\n", encoding="utf-8")
    grown = [dict(BOOKS[1])]
    grown[0]["highlights"] = BOOKS[1]["highlights"] + [
        {"id": 4, "text": "Focus is the new IQ.", "location": 900,
         "highlighted_at": "2026-06-05T10:00:00Z", "note": ""}]
    res = ingest_readwise(vault, "tok", apply=True, books=grown)
    assert res["new_highlights"] == 1
    text = deep.read_text()
    assert "MY OWN THOUGHTS" in text and "Focus is the new IQ." in text
    assert len(list((vault.root / "inbox").glob("*.md"))) == 2


def test_since_overrides_cursor(vault):
    res = ingest_readwise(vault, "tok", since="2026-07-01T00:00:00Z", books=BOOKS)
    assert res["since"] == "2026-07-01T00:00:00Z"


def test_cli_requires_token(vault, capsys, monkeypatch):
    from memex_cli import cli

    monkeypatch.delenv("READWISE_TOKEN", raising=False)
    code = cli.main(["ingest", "readwise", "--vault", str(vault.root)])
    _, err = capsys.readouterr()
    assert code == 1 and "READWISE_TOKEN" in err


def test_cli_end_to_end(vault, capsys, monkeypatch):
    from memex_cli import cli

    monkeypatch.setenv("READWISE_TOKEN", "tok")
    monkeypatch.setattr("memex_cli.ingest_readwise.fetch_export",
                        lambda token, updated_after: BOOKS)
    code = cli.main(["ingest", "readwise", "--vault", str(vault.root)])
    out, err = capsys.readouterr()
    assert code == 0 and "dry-run: would capture 3" in out
    event = json.loads(err.strip().splitlines()[-1])
    assert event["cmd"] == "ingest-readwise" and not event["applied"]

    code = cli.main(["ingest", "readwise", "--vault", str(vault.root), "--apply"])
    out, _ = capsys.readouterr()
    assert code == 0 and "captured 3 new highlight(s)" in out
