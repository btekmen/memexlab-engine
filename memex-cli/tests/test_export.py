"""Tests for export with mandatory grade gate."""
import pathlib

import pytest

from memex_cli.export import export_note
from memex_cli.vault import Vault, parse_frontmatter


@pytest.fixture
def vault(tmp_path: pathlib.Path) -> Vault:
    """Create a test vault with sample notes."""
    (tmp_path / "governance.yml").write_text("write_dir: inbox\n", encoding="utf-8")
    
    # Create a concept note in canonical directory
    concepts = tmp_path / "concepts"
    concepts.mkdir()
    concept_note = concepts / "platform-banking.md"
    concept_note.write_text(
        "---\n"
        "type: concept\n"
        "title: Platform Banking\n"
        "---\n"
        "# Platform Banking\n\n"
        "Platform banking is about embedding financial services.\n",
        encoding="utf-8"
    )
    
    # Create a person note in canonical directory
    people = tmp_path / "people"
    people.mkdir()
    person_note = people / "ada-stone.md"
    person_note.write_text(
        "---\n"
        "type: person\n"
        "title: Ada Stone\n"
        "---\n"
        "# Ada Stone\n\n"
        "Researcher.\n",
        encoding="utf-8"
    )
    
    # Create an inbox note (non-canonical)
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    inbox_note = inbox / "test-note.md"
    inbox_note.write_text(
        "---\n"
        "title: Test Note\n"
        "---\n"
        "# Test Note\n\n"
        "This is a test.\n",
        encoding="utf-8"
    )
    
    return Vault(tmp_path)


def test_missing_grade_fails(vault):
    """Export without --grade must fail."""
    result = export_note(vault, "platform-banking", grade=None, apply=False)
    assert not result["ok"]
    assert result["action"] == "missing-grade"
    assert "requires explicit --grade" in result["error"]
    assert not result["applied"]


def test_invalid_grade_fails(vault):
    """Export with invalid grade must fail."""
    result = export_note(vault, "platform-banking", grade="invalid", apply=False)
    assert not result["ok"]
    assert result["action"] == "invalid-grade"
    assert result["provided"] == "invalid"
    assert not result["applied"]


def test_missing_note_fails(vault):
    """Export of non-existent note must fail."""
    result = export_note(vault, "nonexistent-note", grade="public", apply=False)
    assert not result["ok"]
    assert result["action"] == "note-not-found"
    assert not result["applied"]


def test_dry_run_writes_nothing(vault):
    """Dry-run export must not create any files."""
    result = export_note(vault, "platform-banking", grade="public", apply=False)
    assert result["ok"]
    assert not result["applied"]
    assert result["grade"] == "public"
    assert result["source_note"] == "concepts/platform-banking.md"
    assert result["export_path"].startswith("exports/")
    assert result["canonical_source"]
    
    # Verify exports directory was not created
    exports_dir = vault.root / "exports"
    assert not exports_dir.exists()


def test_apply_writes_export_file(vault):
    """Apply must write the graded export file."""
    result = export_note(vault, "platform-banking", grade="internal", apply=True)
    assert result["ok"]
    assert result["applied"]
    assert result["grade"] == "internal"
    
    # Verify export file exists
    export_path = vault.root / result["export_path"]
    assert export_path.exists()
    assert export_path.parent.name == "exports"
    
    # Verify content has grade metadata
    content = export_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    assert meta["export_grade"] == "internal"
    assert meta["export_source"] == "concepts/platform-banking.md"
    assert "export_timestamp" in meta
    assert "Platform banking is about embedding" in body


def test_canonical_directories_untouched(vault):
    """Exports must never write to canonical directories."""
    result = export_note(vault, "platform-banking", grade="public", apply=True)
    assert result["ok"]
    
    # Verify canonical directory unchanged
    concepts_dir = vault.root / "concepts"
    original_note = concepts_dir / "platform-banking.md"
    content = original_note.read_text(encoding="utf-8")
    
    # Original note must not have export metadata
    meta, _ = parse_frontmatter(content)
    assert "export_grade" not in meta
    assert "export_timestamp" not in meta
    
    # Export must be in exports/ directory only
    export_path = vault.root / result["export_path"]
    assert export_path.parts[0] != "concepts"
    assert export_path.parts[0] != "people"
    assert export_path.parts[0] != "companies"


def test_all_three_grades_work(vault):
    """All three valid grades (private, internal, public) must work."""
    for grade in ["private", "internal", "public"]:
        result = export_note(vault, "test-note", grade=grade, apply=True)
        assert result["ok"]
        assert result["grade"] == grade
        
        export_path = vault.root / result["export_path"]
        assert export_path.exists()
        content = export_path.read_text(encoding="utf-8")
        meta, _ = parse_frontmatter(content)
        assert meta["export_grade"] == grade


def test_export_by_path(vault):
    """Export must work with relative path instead of slug."""
    result = export_note(vault, "concepts/platform-banking.md", grade="public", apply=True)
    assert result["ok"]
    assert result["source_note"] == "concepts/platform-banking.md"


def test_export_by_slug(vault):
    """Export must work with note slug."""
    result = export_note(vault, "platform-banking", grade="public", apply=True)
    assert result["ok"]
    assert result["source_note"] == "concepts/platform-banking.md"


def test_exported_by_metadata(vault):
    """Export must record exported_by when provided."""
    result = export_note(
        vault, 
        "test-note", 
        grade="private", 
        apply=True,
        exported_by="test-user"
    )
    assert result["ok"]
    
    export_path = vault.root / result["export_path"]
    content = export_path.read_text(encoding="utf-8")
    meta, _ = parse_frontmatter(content)
    assert meta["exported_by"] == "test-user"


def test_export_preserves_original_frontmatter(vault):
    """Export must preserve original note frontmatter."""
    result = export_note(vault, "platform-banking", grade="public", apply=True)
    assert result["ok"]
    
    export_path = vault.root / result["export_path"]
    content = export_path.read_text(encoding="utf-8")
    meta, _ = parse_frontmatter(content)
    
    # Original frontmatter preserved
    assert meta["type"] == "concept"
    assert meta["title"] == "Platform Banking"
    
    # Export metadata added
    assert meta["export_grade"] == "public"
    assert meta["export_source"] == "concepts/platform-banking.md"


def test_non_canonical_directory_has_no_warning(vault):
    """Notes from non-canonical directories should not trigger warning."""
    result = export_note(vault, "test-note", grade="public", apply=False)
    assert result["ok"]
    assert not result["canonical_source"]


def test_multiple_exports_dont_conflict(vault):
    """Multiple exports of the same note must create different files."""
    result1 = export_note(vault, "test-note", grade="public", apply=True)
    result2 = export_note(vault, "test-note", grade="private", apply=True)
    
    assert result1["ok"] and result2["ok"]
    assert result1["export_path"] != result2["export_path"]
    
    export1 = vault.root / result1["export_path"]
    export2 = vault.root / result2["export_path"]
    assert export1.exists() and export2.exists()
