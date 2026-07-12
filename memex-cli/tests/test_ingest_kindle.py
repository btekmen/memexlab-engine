import json
import pathlib

import pytest

from memex_cli.ingest_kindle import ingest_kindle, parse_clippings
from memex_cli.vault import Vault

CLIPPINGS = (
    "﻿Deep Work (Cal Newport)\r\n"
    "- Your Highlight on page 23 | Location 345-347 | Added on Monday, July 1, 2024 10:00:12 AM\r\n"
    "\r\n"
    "Clarity about what matters provides clarity about what does not.\r\n"
    "==========\r\n"
    "Deep Work (Cal Newport)\r\n"
    "- Your Note on page 23 | Location 347 | Added on Monday, July 1, 2024 10:01:00 AM\r\n"
    "\r\n"
    "Connect this to the latticework problem of focus.\r\n"
    "==========\r\n"
    "Deep Work (Cal Newport)\r\n"
    "- Your Bookmark on Location 400 | Added on Monday, July 1, 2024 10:02:00 AM\r\n"
    "\r\n"
    "==========\r\n"
    "As We May Think (Vannevar Bush)\r\n"
    "- Your Highlight on Location 120-125 | Added on Tuesday, July 2, 2024 08:30:00 PM\r\n"
    "\r\n"
    "The human mind operates by association.\r\n"
    "==========\r\n"
)


@pytest.fixture
def vault(tmp_path: pathlib.Path) -> Vault:
    (tmp_path / "governance.yml").write_text("write_dir: inbox\n", encoding="utf-8")
    return Vault(tmp_path)


@pytest.fixture
def clippings_file(tmp_path: pathlib.Path) -> pathlib.Path:
    f = tmp_path / "My Clippings.txt"
    f.write_text(CLIPPINGS, encoding="utf-8")
    return f


def test_parser_handles_variants_and_drops_bookmarks():
    entries = parse_clippings(CLIPPINGS)
    assert [e["kind"] for e in entries] == ["Highlight", "Note", "Highlight"]
    assert entries[0]["page"] == "23" and entries[0]["loc"] == "345-347"
    assert entries[2]["title"] == "As We May Think"
    assert entries[2]["author"] == "Vannevar Bush"


def test_dry_run_writes_nothing(vault, clippings_file):
    res = ingest_kindle(vault, str(clippings_file), apply=False)
    assert res["ok"] and res["books"] == 2 and res["new_highlights"] == 3
    assert not (vault.root / "inbox").exists()
    assert not (vault.root / ".memex").exists()


def test_apply_creates_one_note_per_book(vault, clippings_file):
    res = ingest_kindle(vault, str(clippings_file), apply=True)
    notes = sorted((vault.root / "inbox").glob("*.md"))
    assert len(notes) == 2
    deep = next(n for n in notes if "deep-work" in n.name).read_text()
    assert "title: Deep Work" in deep
    assert "source_author: Cal Newport" in deep
    assert "captured_via: kindle" in deep
    assert "> Clarity about what matters" in deep
    assert "**Note.**" in deep
    assert "page 23 · loc 345-347" in deep
    assert res["new_highlights"] == 3


def test_double_import_adds_nothing(vault, clippings_file):
    ingest_kindle(vault, str(clippings_file), apply=True)
    before = {p.name: p.read_text() for p in (vault.root / "inbox").glob("*.md")}
    res = ingest_kindle(vault, str(clippings_file), apply=True)
    after = {p.name: p.read_text() for p in (vault.root / "inbox").glob("*.md")}
    assert res["new_highlights"] == 0 and res["known_skipped"] == 3
    assert before == after


def test_extended_file_appends_only_new(vault, clippings_file, tmp_path):
    ingest_kindle(vault, str(clippings_file), apply=True)
    extended = CLIPPINGS + (
        "Deep Work (Cal Newport)\r\n"
        "- Your Highlight on page 99 | Location 900-901 | Added on Wednesday, July 3, 2024 09:00:00 AM\r\n"
        "\r\n"
        "A deep life is a good life.\r\n"
        "==========\r\n"
    )
    f2 = tmp_path / "My Clippings 2.txt"
    f2.write_text(extended, encoding="utf-8")
    res = ingest_kindle(vault, str(f2), apply=True)
    assert res["new_highlights"] == 1 and res["known_skipped"] == 3
    notes = list((vault.root / "inbox").glob("*.md"))
    assert len(notes) == 2  # appended, not duplicated
    deep = next(n for n in notes if "deep-work" in n.name).read_text()
    assert "A deep life is a good life." in deep


def test_user_edits_survive_reimport(vault, clippings_file, tmp_path):
    ingest_kindle(vault, str(clippings_file), apply=True)
    deep = next(p for p in (vault.root / "inbox").glob("*.md") if "deep-work" in p.name)
    deep.write_text(deep.read_text() + "\nMY OWN THOUGHTS\n", encoding="utf-8")
    extended = CLIPPINGS + (
        "Deep Work (Cal Newport)\r\n"
        "- Your Highlight on page 100 | Location 950 | Added on Thursday, July 4, 2024 09:00:00 AM\r\n"
        "\r\n"
        "Focus is the new IQ.\r\n"
        "==========\r\n"
    )
    f2 = tmp_path / "c3.txt"
    f2.write_text(extended, encoding="utf-8")
    ingest_kindle(vault, str(f2), apply=True)
    text = deep.read_text()
    assert "MY OWN THOUGHTS" in text and "Focus is the new IQ." in text


def test_cli_end_to_end(vault, clippings_file, capsys):
    from memex_cli import cli

    code = cli.main(["ingest", "kindle", str(clippings_file), "--vault", str(vault.root)])
    out, err = capsys.readouterr()
    assert code == 0 and "dry-run: would capture 3" in out and "Use --apply" in out
    event = json.loads(err.strip().splitlines()[-1])
    assert event["cmd"] == "ingest-kindle" and not event["applied"]

    code = cli.main(["ingest", "kindle", str(clippings_file), "--vault", str(vault.root), "--apply"])
    out, _ = capsys.readouterr()
    assert code == 0 and "captured 3 new highlight(s)" in out

    code = cli.main(["ingest", "kindle", "/nonexistent.txt", "--vault", str(vault.root)])
    assert code == 1
