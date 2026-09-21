import pathlib
import re
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


# --- frontmatter injection ----------------------------------------------------
# An .ics file is attacker-controlled: anyone who can email a calendar invite
# picks these values. They must never be able to add frontmatter keys, forge
# type:/tags:, or terminate the frontmatter block.

def frontmatter(text: str) -> dict:
    """Parse the frontmatter block — closing fence on a line of its own."""
    yaml = pytest.importorskip("yaml")
    m = re.search(r"\A---\n(.*?)^---\s*$", text, re.S | re.M)
    assert m, "note has no frontmatter block"
    return yaml.safe_load(m.group(1))


def _ics(*props):
    return "\r\n".join(["BEGIN:VCALENDAR", "BEGIN:VEVENT", *props,
                        "END:VEVENT", "END:VCALENDAR", ""])


HOSTILE_LOCATION = _ics(
    "UID:evt-hostile@example.com",
    "DTSTART:20260715T150000Z",
    "SUMMARY:Quarterly sync",
    # \n in an ICS value is unescaped to a real newline by _unescape
    "LOCATION:Zoom\\ntype: person\\ntags:\\n  - trusted\\nowner: attacker",
)

TERMINATOR_LOCATION = _ics(
    "UID:evt-terminator@example.com",
    "DTSTART:20260715T150000Z",
    "SUMMARY:Quarterly sync",
    "LOCATION:Zoom\\n---\\ntype: person\\n---\\nforged body",
)

METACHAR_LOCATION = _ics(
    "UID:evt-meta@example.com",
    "DTSTART:20260715T150000Z",
    "SUMMARY:Quarterly sync",
    "LOCATION:*anchor &ref !!python/object:os.system [a\\, b] {x: y} #c",
)

HOSTILE_DTSTART = _ics(
    "UID:evt-dtstart@example.com",
    "DTSTART:{not-a-date: [",
    "SUMMARY:Quarterly sync",
)


def test_hostile_location_cannot_inject_frontmatter_keys(tmp_path, vault):
    ics = write_ics(tmp_path, HOSTILE_LOCATION)
    ingest_ics.main([str(ics), "--vault", str(vault), "--apply"])
    fm = frontmatter(next((vault / "inbox").glob("*.md")).read_text(encoding="utf-8"))
    assert fm["type"] == "meeting"
    assert fm["source"] == "ics"
    assert "tags" not in fm and "owner" not in fm
    assert fm["location"].startswith("Zoom")
    assert "type: person" in fm["location"]


def test_hostile_location_cannot_terminate_the_block(tmp_path, vault):
    ics = write_ics(tmp_path, TERMINATOR_LOCATION)
    ingest_ics.main([str(ics), "--vault", str(vault), "--apply"])
    text = next((vault / "inbox").glob("*.md")).read_text(encoding="utf-8")
    fm = frontmatter(text)
    assert fm["type"] == "meeting"
    assert "---" in fm["location"]


def test_yaml_metacharacters_survive_as_literal_text(tmp_path, vault):
    ics = write_ics(tmp_path, METACHAR_LOCATION)
    ingest_ics.main([str(ics), "--vault", str(vault), "--apply"])
    fm = frontmatter(next((vault / "inbox").glob("*.md")).read_text(encoding="utf-8"))
    assert fm["type"] == "meeting"
    assert isinstance(fm["location"], str)
    assert fm["location"].startswith("*anchor &ref")


def test_unparseable_dtstart_still_yields_valid_frontmatter(tmp_path, vault):
    ics = write_ics(tmp_path, HOSTILE_DTSTART)
    ingest_ics.main([str(ics), "--vault", str(vault), "--apply"])
    fm = frontmatter(next((vault / "inbox").glob("*.md")).read_text(encoding="utf-8"))
    assert fm["type"] == "meeting"
    assert isinstance(fm["date"], str)


def test_hostile_invite_still_dedupes_on_reingest(tmp_path, vault):
    ics = write_ics(tmp_path, HOSTILE_LOCATION)
    ingest_ics.main([str(ics), "--vault", str(vault), "--apply"])
    ingest_ics.main([str(ics), "--vault", str(vault), "--apply"])
    assert len(list((vault / "inbox").glob("*.md"))) == 1


TRAVERSAL_DTSTART = _ics(
    "UID:evt-traversal@example.com",
    "DTSTART:../../../../tmp/pwned",
    "SUMMARY:Quarterly sync",
)


def test_hostile_dtstart_cannot_escape_the_inbox(tmp_path, vault):
    ics = write_ics(tmp_path, TRAVERSAL_DTSTART)
    ingest_ics.main([str(ics), "--vault", str(vault), "--apply"])
    written = list((vault / "inbox").glob("*.md"))
    assert len(written) == 1
    assert written[0].resolve().parent == (vault / "inbox").resolve()
    assert not (tmp_path / "pwned-quarterly-sync.md").exists()
