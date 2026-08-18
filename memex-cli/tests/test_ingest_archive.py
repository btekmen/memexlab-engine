"""Tests for archive ingest (LinkedIn, Matter, Books)."""
import json
import pathlib
import zipfile

import pytest

from memex_cli.ingest_archive import (
    ingest_archive,
    _parse_linkedin_connections_csv,
    _parse_matter_export,
    _parse_books_csv,
)
from memex_cli.vault import Vault


LINKEDIN_CSV = """First Name,Last Name,Email Address,Company,Position,Connected On
Alice,Chen,alice.chen@example.com,TechCorp,Senior Engineer,15 Jan 2024
Bob,Martinez,,StartupX,Product Manager,22 Feb 2024
Carol,Johnson,carol.j@example.org,FinanceInc,Data Analyst,10 Mar 2024
"""

MATTER_JSON = """[
  {
    "title": "The Future of AI in 2024",
    "url": "https://example.com/ai-future-2024",
    "author": "Jane Smith",
    "content": "A comprehensive look at emerging AI trends.",
    "saved_at": "2024-01-15T10:30:00Z"
  },
  {
    "title": "Building Resilient Systems",
    "url": "https://example.com/resilient-systems",
    "author": "John Doe",
    "content": "Best practices for designing systems.",
    "saved_at": "2024-02-20T14:45:00Z"
  }
]"""

BOOKS_CSV = """title,author,shelf
Thinking Fast and Slow,Daniel Kahneman,read
The Design of Everyday Things,Don Norman,reading
Sapiens,Yuval Noah Harari,to-read
"""


@pytest.fixture
def vault(tmp_path: pathlib.Path) -> Vault:
    (tmp_path / "governance.yml").write_text("write_dir: inbox\n", encoding="utf-8")
    return Vault(tmp_path)


@pytest.fixture
def linkedin_csv_file(tmp_path: pathlib.Path) -> pathlib.Path:
    f = tmp_path / "Connections.csv"
    f.write_text(LINKEDIN_CSV, encoding="utf-8")
    return f


@pytest.fixture
def linkedin_zip_file(tmp_path: pathlib.Path) -> pathlib.Path:
    z = tmp_path / "linkedin.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("Connections.csv", LINKEDIN_CSV)
    return z


@pytest.fixture
def matter_json_file(tmp_path: pathlib.Path) -> pathlib.Path:
    f = tmp_path / "matter-export.json"
    f.write_text(MATTER_JSON, encoding="utf-8")
    return f


@pytest.fixture
def books_csv_file(tmp_path: pathlib.Path) -> pathlib.Path:
    f = tmp_path / "books.csv"
    f.write_text(BOOKS_CSV, encoding="utf-8")
    return f


def test_parse_linkedin_connections():
    connections = _parse_linkedin_connections_csv(LINKEDIN_CSV)
    assert len(connections) == 3
    assert connections[0]["first_name"] == "Alice"
    assert connections[0]["last_name"] == "Chen"
    assert connections[0]["email"] == "alice.chen@example.com"
    assert connections[0]["company"] == "TechCorp"
    assert connections[1]["email"] == ""  # Bob has no email


def test_parse_matter_export():
    articles = _parse_matter_export(MATTER_JSON)
    assert len(articles) == 2
    assert articles[0]["title"] == "The Future of AI in 2024"
    assert articles[0]["url"] == "https://example.com/ai-future-2024"
    assert articles[0]["author"] == "Jane Smith"
    assert articles[1]["author"] == "John Doe"


def test_parse_books_csv():
    books = _parse_books_csv(BOOKS_CSV)
    assert len(books) == 3
    assert books[0]["title"] == "Thinking Fast and Slow"
    assert books[0]["author"] == "Daniel Kahneman"
    assert books[0]["shelf"] == "read"
    assert books[2]["shelf"] == "to-read"


def test_linkedin_dry_run_writes_nothing(vault, linkedin_csv_file):
    res = ingest_archive(vault, str(linkedin_csv_file), kind="linkedin", apply=False)
    assert res["ok"]
    assert res["new_items"] == 3
    assert res["known_skipped"] == 0
    assert not (vault.root / "inbox").exists()
    assert len(res["plan"]) == 3
    assert all(p["type"] == "connection" for p in res["plan"])


def test_linkedin_apply_creates_notes(vault, linkedin_csv_file):
    res = ingest_archive(vault, str(linkedin_csv_file), kind="linkedin", apply=True)
    assert res["ok"]
    assert res["applied"]
    notes = sorted((vault.root / "inbox").glob("*.md"))
    assert len(notes) == 3
    
    # Check Alice Chen's note
    alice_note = next(n for n in notes if "alice-chen" in n.name).read_text()
    assert "title: Alice Chen" in alice_note
    assert "captured_via: linkedin-archive" in alice_note
    assert "contact_email: alice.chen@example.com" in alice_note
    assert "source_company: TechCorp" in alice_note
    assert "**Position:** Senior Engineer" in alice_note


def test_linkedin_from_zip(vault, linkedin_zip_file):
    res = ingest_archive(vault, str(linkedin_zip_file), kind="linkedin", apply=True)
    assert res["ok"]
    assert res["new_items"] == 3
    notes = list((vault.root / "inbox").glob("*.md"))
    assert len(notes) == 3


def test_matter_apply_creates_notes(vault, matter_json_file):
    res = ingest_archive(vault, str(matter_json_file), kind="matter", apply=True)
    assert res["ok"]
    assert res["applied"]
    assert res["new_items"] == 2
    notes = sorted((vault.root / "inbox").glob("*.md"))
    assert len(notes) == 2
    
    # Check first article
    ai_note = next(n for n in notes if "future-of-ai" in n.name).read_text()
    assert "title: The Future of AI in 2024" in ai_note
    assert "captured_via: matter-export" in ai_note
    assert "source_url: https://example.com/ai-future-2024" in ai_note
    assert "source_author: Jane Smith" in ai_note
    assert "**Author:** Jane Smith" in ai_note


def test_books_apply_creates_notes(vault, books_csv_file):
    res = ingest_archive(vault, str(books_csv_file), kind="books", apply=True)
    assert res["ok"]
    assert res["applied"]
    assert res["new_items"] == 3
    notes = sorted((vault.root / "inbox").glob("*.md"))
    assert len(notes) == 3
    
    # Check first book
    thinking_note = next(n for n in notes if "thinking-fast-and-slow" in n.name).read_text()
    assert "title: Thinking Fast and Slow" in thinking_note
    assert "captured_via: books-archive" in thinking_note
    assert "source_author: Daniel Kahneman" in thinking_note
    assert "shelf: read" in thinking_note
    assert "**Shelf:** read" in thinking_note


def test_double_import_adds_nothing(vault, linkedin_csv_file):
    ingest_archive(vault, str(linkedin_csv_file), kind="linkedin", apply=True)
    before = {p.name: p.read_text() for p in (vault.root / "inbox").glob("*.md")}
    res = ingest_archive(vault, str(linkedin_csv_file), kind="linkedin", apply=True)
    after = {p.name: p.read_text() for p in (vault.root / "inbox").glob("*.md")}
    assert res["new_items"] == 0
    assert res["known_skipped"] == 3
    assert before == after


def test_writes_only_to_inbox(vault, linkedin_csv_file):
    """Ensure notes are only written to inbox/, never to wiki/, people/, etc."""
    ingest_archive(vault, str(linkedin_csv_file), kind="linkedin", apply=True)
    
    # Verify inbox has files
    assert (vault.root / "inbox").exists()
    assert len(list((vault.root / "inbox").glob("*.md"))) == 3
    
    # Verify canonical directories don't exist (not created by ingest)
    assert not (vault.root / "wiki").exists()
    assert not (vault.root / "people").exists()
    assert not (vault.root / "companies").exists()


def test_missing_file_raises_error(vault):
    with pytest.raises(FileNotFoundError):
        ingest_archive(vault, "/nonexistent.csv", kind="linkedin", apply=False)


def test_unknown_kind_raises_error(vault, linkedin_csv_file):
    with pytest.raises(ValueError, match="Unknown archive kind"):
        ingest_archive(vault, str(linkedin_csv_file), kind="unknown", apply=False)


def test_cli_linkedin_end_to_end(vault, linkedin_csv_file, capsys):
    from memex_cli import cli

    # Dry run
    code = cli.main([
        "ingest", "archive", str(linkedin_csv_file),
        "--kind", "linkedin",
        "--vault", str(vault.root)
    ])
    out, err = capsys.readouterr()
    assert code == 0
    assert "dry-run: would capture 3" in out
    assert "Use --apply" in out
    event = json.loads(err.strip().splitlines()[-1])
    assert event["cmd"] == "ingest-archive"
    assert not event["applied"]

    # Apply
    code = cli.main([
        "ingest", "archive", str(linkedin_csv_file),
        "--kind", "linkedin",
        "--vault", str(vault.root),
        "--apply"
    ])
    out, _ = capsys.readouterr()
    assert code == 0
    assert "captured 3 new linkedin item(s)" in out


def test_cli_matter_end_to_end(vault, matter_json_file, capsys):
    from memex_cli import cli

    code = cli.main([
        "ingest", "archive", str(matter_json_file),
        "--kind", "matter",
        "--vault", str(vault.root),
        "--apply"
    ])
    out, _ = capsys.readouterr()
    assert code == 0
    assert "captured 2 new matter item(s)" in out


def test_cli_books_end_to_end(vault, books_csv_file, capsys):
    from memex_cli import cli

    code = cli.main([
        "ingest", "archive", str(books_csv_file),
        "--kind", "books",
        "--vault", str(vault.root),
        "--apply"
    ])
    out, _ = capsys.readouterr()
    assert code == 0
    assert "captured 3 new books item(s)" in out


def test_cli_missing_file_returns_error(vault, capsys):
    from memex_cli import cli

    code = cli.main([
        "ingest", "archive", "/nonexistent.csv",
        "--kind", "linkedin",
        "--vault", str(vault.root)
    ])
    out, err = capsys.readouterr()
    assert code == 1
    assert "error: no such file" in err
