import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import ingest_ics  # noqa: E402

SAMPLE = "\r\n".join([
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Example//Calendar//EN",
    "BEGIN:VEVENT",
    "UID:evt-123@example.com",
    "DTSTART;TZID=Europe/Istanbul:20260715T150000",
    "DTEND;TZID=Europe/Istanbul:20260715T160000",
    "SUMMARY:Board prep\\, Q3 review",
    "LOCATION:Zoom",
    "ORGANIZER;CN=Ada Stone:mailto:ada@acmebank.example",
    "ATTENDEE;CN=Ada Stone;ROLE=CHAIR:mailto:ada@acmebank.example",
    "ATTENDEE;CN=Bulent Tekmen:mailto:bulent@example.com",
    "DESCRIPTION:Agenda:\\n1. Numbers\\n2. Risks",
    "END:VEVENT",
    "END:VCALENDAR",
    "",
])

FOLDED = "\r\n".join([
    "BEGIN:VCALENDAR",
    "BEGIN:VEVENT",
    "UID:evt-folded",
    "DTSTART;VALUE=DATE:20260716",
    "SUMMARY:A very long summary that got fold",
    " ed across two lines",
    "END:VEVENT",
    "END:VCALENDAR",
    "",
])


@pytest.fixture
def vault(tmp_path):
    (tmp_path / "inbox").mkdir()
    return tmp_path


def write_ics(tmp_path, body, name="invite.ics"):
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def test_parses_event_fields(tmp_path):
    events = ingest_ics.parse_ics(write_ics(tmp_path, SAMPLE))
    assert len(events) == 1
    e = events[0]
    assert e["uid"] == "evt-123@example.com"
    assert e["summary"] == "Board prep, Q3 review"
    assert e["dtstart"] == "2026-07-15T15:00:00"
    assert e["location"] == "Zoom"
    assert e["organizer"] == {"name": "Ada Stone", "email": "ada@acmebank.example"}
    assert {"name": "Bulent Tekmen", "email": "bulent@example.com"} in e["attendees"]
    assert len(e["attendees"]) == 2
    assert "1. Numbers" in e["description"]


def test_unfolds_lines_and_all_day_dates(tmp_path):
    events = ingest_ics.parse_ics(write_ics(tmp_path, FOLDED))
    e = events[0]
    assert e["summary"] == "A very long summary that got folded across two lines"
    assert e["dtstart"] == "2026-07-16"


def test_dry_run_by_default_writes_nothing(tmp_path, vault, capsys):
    ics = write_ics(tmp_path, SAMPLE)
    rc = ingest_ics.main([str(ics), "--vault", str(vault)])
    assert rc == 0
    assert list((vault / "inbox").iterdir()) == []
    out = capsys.readouterr().out
    assert "dry-run" in out.lower()
    assert "Board prep" in out


def test_apply_writes_note_with_frontmatter(tmp_path, vault):
    ics = write_ics(tmp_path, SAMPLE)
    rc = ingest_ics.main([str(ics), "--vault", str(vault), "--apply"])
    assert rc == 0
    files = list((vault / "inbox").glob("*.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "type: meeting" in text
    assert "source: ics" in text
    assert "uid: evt-123@example.com" in text
    assert "Board prep, Q3 review" in text
    assert "bulent@example.com" in text


def test_reingest_same_uid_is_idempotent(tmp_path, vault):
    ics = write_ics(tmp_path, SAMPLE)
    ingest_ics.main([str(ics), "--vault", str(vault), "--apply"])
    rc = ingest_ics.main([str(ics), "--vault", str(vault), "--apply"])
    assert rc == 0
    assert len(list((vault / "inbox").glob("*.md"))) == 1


def test_missing_file_fails_loud(vault):
    with pytest.raises(SystemExit):
        ingest_ics.main(["/nonexistent.ics", "--vault", str(vault), "--apply"])
