import pathlib
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
    assert "type: meeting" in text
    assert "source: transcript" in text
    assert "date: 2026-07-15" in text
    assert "  - ada@acmebank.example" in text
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
