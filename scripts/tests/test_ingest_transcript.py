import pathlib
import re
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import ingest_transcript  # noqa: E402

VTT = "\n".join([
    "WEBVTT",
    "",
    "00:00:01.000 --> 00:00:04.000",
    "<v Ada Stone>Welcome everyone, let's start.</v>",
    "",
    "00:00:05.500 --> 00:00:09.000",
    "<v Bulent>Thanks. First item: platform banking.</v>",
    "",
    "00:01:10.000 --> 00:01:12.000",
    "No speaker tag on this one.",
    "",
])

SRT = "\n".join([
    "1",
    "00:00:01,000 --> 00:00:04,000",
    "Ada Stone: Welcome everyone.",
    "",
    "2",
    "00:00:05,500 --> 00:00:09,000",
    "Bulent: First item: platform banking.",
    "",
])

TXT = "\n".join([
    "Ada Stone: Welcome everyone.",
    "Bulent: First item: platform banking.",
    "and a continuation line without a speaker.",
    "",
])


@pytest.fixture
def vault(tmp_path):
    (tmp_path / "inbox").mkdir()
    return tmp_path


def write(tmp_path, name, body):
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def test_parse_vtt_segments_with_speakers(tmp_path):
    segs = ingest_transcript.parse_transcript(write(tmp_path, "m.vtt", VTT))
    assert segs[0] == {"start": "00:00:01", "speaker": "Ada Stone",
                       "text": "Welcome everyone, let's start."}
    assert segs[1]["speaker"] == "Bulent"
    assert segs[2] == {"start": "00:01:10", "speaker": "",
                       "text": "No speaker tag on this one."}


def test_parse_srt_segments(tmp_path):
    segs = ingest_transcript.parse_transcript(write(tmp_path, "m.srt", SRT))
    assert len(segs) == 2
    assert segs[0] == {"start": "00:00:01", "speaker": "Ada Stone",
                       "text": "Welcome everyone."}


def test_parse_txt_speaker_lines(tmp_path):
    segs = ingest_transcript.parse_transcript(write(tmp_path, "m.txt", TXT))
    assert segs[0] == {"start": "", "speaker": "Ada Stone",
                       "text": "Welcome everyone."}
    assert segs[2]["speaker"] == ""
    assert segs[2]["text"] == "and a continuation line without a speaker."


def test_dry_run_by_default_writes_nothing(tmp_path, vault, capsys):
    f = write(tmp_path, "m.vtt", VTT)
    rc = ingest_transcript.main([str(f), "--vault", str(vault),
                                 "--title", "Q3 sync", "--date", "2026-07-15"])
    assert rc == 0
    assert list((vault / "inbox").iterdir()) == []
    assert "dry-run" in capsys.readouterr().out.lower()


def test_apply_writes_note_with_frontmatter_and_quotes(tmp_path, vault):
    f = write(tmp_path, "m.vtt", VTT)
    rc = ingest_transcript.main([str(f), "--vault", str(vault), "--apply",
                                 "--title", "Q3 sync", "--date", "2026-07-15",
                                 "--attendees", "ada@acmebank.example,bulent@example.com"])
    assert rc == 0
    files = list((vault / "inbox").glob("*.md"))
    assert len(files) == 1
    assert files[0].name == "meeting-2026-07-15-q3-sync.md"
    text = files[0].read_text(encoding="utf-8")
    assert text.startswith("---\n")
    # frontmatter is yaml.safe_dump output, so assert on the parsed mapping
    # rather than on one particular scalar style
    fm = frontmatter(text)
    assert fm["type"] == "meeting"
    assert fm["source"] == "transcript"
    assert fm["date"] == "2026-07-15"
    assert fm["attendees"] == ["ada@acmebank.example", "bulent@example.com"]
    assert "> [00:00:01] **Ada Stone**: Welcome everyone, let's start." in text


def test_reingest_same_content_is_idempotent(tmp_path, vault):
    f = write(tmp_path, "m.vtt", VTT)
    args = [str(f), "--vault", str(vault), "--apply",
            "--title", "Q3 sync", "--date", "2026-07-15"]
    ingest_transcript.main(args)
    rc = ingest_transcript.main(args)
    assert rc == 0
    assert len(list((vault / "inbox").glob("*.md"))) == 1


def test_unknown_extension_fails_loud(tmp_path, vault):
    f = write(tmp_path, "m.docx", "not a transcript")
    with pytest.raises(SystemExit):
        ingest_transcript.main([str(f), "--vault", str(vault), "--apply"])


# --- frontmatter injection ----------------------------------------------------

def frontmatter(text: str) -> dict:
    """Parse the frontmatter block — closing fence on a line of its own."""
    yaml = pytest.importorskip("yaml")
    m = re.search(r"\A---\n(.*?)^---\s*$", text, re.S | re.M)
    assert m, "note has no frontmatter block"
    return yaml.safe_load(m.group(1))


def test_hostile_date_cannot_inject_frontmatter(tmp_path, vault):
    f = write(tmp_path, "m.vtt", VTT)
    ingest_transcript.main([str(f), "--vault", str(vault), "--apply",
                            "--title", "Q3 sync",
                            "--date", "2026-07-15\ntype: person\ntags:\n  - trusted"])
    fm = frontmatter(next((vault / "inbox").glob("*.md")).read_text(encoding="utf-8"))
    assert fm["type"] == "meeting"
    assert "tags" not in fm
    assert isinstance(fm["date"], str)


def test_hostile_attendee_cannot_terminate_the_block(tmp_path, vault):
    f = write(tmp_path, "m.vtt", VTT)
    ingest_transcript.main([str(f), "--vault", str(vault), "--apply",
                            "--title", "Q3 sync",
                            "--attendees", "ada@example.com\n---\ntype: person\n---\n"])
    fm = frontmatter(next((vault / "inbox").glob("*.md")).read_text(encoding="utf-8"))
    assert fm["type"] == "meeting"
    assert fm["source"] == "transcript"
    assert isinstance(fm["attendees"], list) and len(fm["attendees"]) == 1


def test_transcript_frontmatter_is_valid_yaml_with_metacharacters(tmp_path, vault):
    f = write(tmp_path, "m.vtt", VTT)
    ingest_transcript.main([str(f), "--vault", str(vault), "--apply",
                            "--title", "Q3 sync", "--date", "*anchor &ref {x: y}"])
    fm = frontmatter(next((vault / "inbox").glob("*.md")).read_text(encoding="utf-8"))
    assert fm["date"] == "*anchor &ref {x: y}"


def test_hostile_date_cannot_escape_the_inbox(tmp_path, vault):
    f = write(tmp_path, "m.vtt", VTT)
    ingest_transcript.main([str(f), "--vault", str(vault), "--apply",
                            "--title", "Q3 sync", "--date", "../../../../tmp/pwned"])
    written = list((vault / "inbox").glob("*.md"))
    assert len(written) == 1
    assert written[0].resolve().parent == (vault / "inbox").resolve()
