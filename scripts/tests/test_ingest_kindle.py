import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import ingest_kindle  # noqa: E402

SEP = "=========="

CLIPPINGS = "\r\n".join([
    "The Innovator's Dilemma (Clayton M. Christensen)",
    "- Your Highlight on page 23 | location 340-345 | Added on Monday, July 14, 2026 10:23:45 AM",
    "",
    "Disruptive technologies bring to market a very different value proposition.",
    SEP,
    "The Innovator's Dilemma (Clayton M. Christensen)",
    "- Your Note on page 24 | location 350 | Added on Monday, July 14, 2026 10:25:00 AM",
    "",
    "Compare with aggregation theory.",
    SEP,
    "Zero to One (Peter Thiel)",
    "- Your Highlight at location 120-124 | Added on Tuesday, July 15, 2026 9:00:00 PM",
    "",
    "Competition is for losers.",
    SEP,
    "Zero to One (Peter Thiel)",
    "- Your Bookmark at location 200 | Added on Tuesday, July 15, 2026 9:05:00 PM",
    "",
    "",
    SEP,
    "",
])

MALFORMED = "\r\n".join([
    "Some Book (Author)",
    "- Something unrecognizable entirely",
    "",
    "text",
    SEP,
    "",
])


@pytest.fixture
def vault(tmp_path):
    (tmp_path / "raw").mkdir()
    return tmp_path


def write(tmp_path, body, name="My Clippings.txt"):
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def test_parses_highlight_fields(tmp_path):
    clips = ingest_kindle.parse_clippings(write(tmp_path, CLIPPINGS))
    c = clips[0]
    assert c["title"] == "The Innovator's Dilemma"
    assert c["author"] == "Clayton M. Christensen"
    assert c["kind"] == "highlight"
    assert c["page"] == "23"
    assert c["location"] == "340-345"
    assert c["date"] == "2026-07-14"
    assert c["text"].startswith("Disruptive technologies")


def test_note_kind_and_bookmark_skipped(tmp_path):
    clips = ingest_kindle.parse_clippings(write(tmp_path, CLIPPINGS))
    kinds = [c["kind"] for c in clips]
    assert kinds == ["highlight", "note", "highlight"]  # bookmark dropped
    assert clips[1]["kind"] == "note"
    assert clips[2]["location"] == "120-124"
    assert clips[2]["page"] == ""


def test_dry_run_by_default_writes_nothing(tmp_path, vault, capsys):
    f = write(tmp_path, CLIPPINGS)
    rc = ingest_kindle.main([str(f), "--vault", str(vault)])
    assert rc == 0
    assert list((vault / "raw").iterdir()) == []
    out = capsys.readouterr().out
    assert "dry-run" in out.lower()
    assert "2 books" in out


def test_apply_writes_one_note_per_book(tmp_path, vault):
    f = write(tmp_path, CLIPPINGS)
    rc = ingest_kindle.main([str(f), "--vault", str(vault), "--apply"])
    assert rc == 0
    files = sorted(p.name for p in (vault / "raw").glob("*.md"))
    assert files == ["kindle-the-innovator-s-dilemma.md", "kindle-zero-to-one.md"]
    text = (vault / "raw" / "kindle-the-innovator-s-dilemma.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "type: source" in text
    assert "source: kindle" in text
    assert "author: Clayton M. Christensen" in text
    assert "> Disruptive technologies bring to market" in text
    assert "page 23" in text and "location 340-345" in text and "2026-07-14" in text
    assert "Compare with aggregation theory." in text  # note kept, marked as note


def test_reimport_merges_never_duplicates(tmp_path, vault):
    f = write(tmp_path, CLIPPINGS)
    ingest_kindle.main([str(f), "--vault", str(vault), "--apply"])
    before = (vault / "raw" / "kindle-zero-to-one.md").read_text(encoding="utf-8")
    ingest_kindle.main([str(f), "--vault", str(vault), "--apply"])
    after = (vault / "raw" / "kindle-zero-to-one.md").read_text(encoding="utf-8")
    assert before == after

    extended = CLIPPINGS + "\r\n".join([
        "Zero to One (Peter Thiel)",
        "- Your Highlight at location 300-301 | Added on Wednesday, July 16, 2026 8:00:00 AM",
        "",
        "The best startups are cults.",
        SEP,
        "",
    ])
    f2 = write(tmp_path, extended, name="My Clippings 2.txt")
    ingest_kindle.main([str(f2), "--vault", str(vault), "--apply"])
    merged = (vault / "raw" / "kindle-zero-to-one.md").read_text(encoding="utf-8")
    assert merged.count("Competition is for losers.") == 1
    assert "The best startups are cults." in merged


def test_malformed_metadata_fails_loud(tmp_path, vault):
    f = write(tmp_path, MALFORMED)
    with pytest.raises(SystemExit):
        ingest_kindle.main([str(f), "--vault", str(vault), "--apply"])
