#!/usr/bin/env python3
"""Tests for scripts/lint_daily.py"""

import json
import pathlib
import subprocess
import tempfile
from datetime import datetime


def test_lint_daily_dry_run():
    """Test that dry-run prints the report path without writing."""
    result = subprocess.run(
        [
            "python3",
            "scripts/lint_daily.py",
            "--vault",
            "examples/fake-vault",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "DRY RUN:" in result.stdout
    assert "_lint/lint-" in result.stdout


def test_lint_daily_write_report():
    """Test that the script creates a properly formatted report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = pathlib.Path(tmpdir) / "test-vault"
        vault_path.mkdir()

        # Create a valid note
        (vault_path / "test.md").write_text(
            """---
type: concept
title: Test Note
status: active
---

# Test Note

A test note.
""",
            encoding="utf-8",
        )

        # Run lint_daily
        test_date = "2026-09-15"
        result = subprocess.run(
            [
                "python3",
                "scripts/lint_daily.py",
                "--vault",
                str(vault_path),
                "--date",
                test_date,
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Lint report written" in result.stdout

        # Check report was created
        report_path = vault_path / "_lint" / f"lint-{test_date}.md"
        assert report_path.exists()

        # Check report content
        report_content = report_path.read_text(encoding="utf-8")
        assert "type: lint-report" in report_content
        assert "# Daily Lint Report" in report_content
        assert "Scan time:" in report_content
        assert "Scanned:" in report_content
        assert "Errors:" in report_content
        assert "Warnings:" in report_content


def test_lint_daily_detects_missing_frontmatter():
    """Test that the script detects notes without frontmatter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = pathlib.Path(tmpdir) / "test-vault"
        vault_path.mkdir()

        # Create a note without frontmatter
        (vault_path / "bad.md").write_text("# Bad Note\n\nNo frontmatter.", encoding="utf-8")

        # Run lint_daily
        test_date = "2026-09-15"
        result = subprocess.run(
            [
                "python3",
                "scripts/lint_daily.py",
                "--vault",
                str(vault_path),
                "--date",
                test_date,
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0  # Exit 0 even with findings

        # Check report shows error
        report_path = vault_path / "_lint" / f"lint-{test_date}.md"
        report_content = report_path.read_text(encoding="utf-8")

        assert "Errors: 1" in report_content
        assert "Missing YAML frontmatter" in report_content


def test_lint_daily_detects_broken_wikilink():
    """Test that the script detects broken wikilinks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = pathlib.Path(tmpdir) / "test-vault"
        vault_path.mkdir()

        # Create a note with broken wikilink
        (vault_path / "test.md").write_text(
            """---
type: concept
title: Test Note
status: active
---

# Test Note

This links to [[nonexistent-note]].
""",
            encoding="utf-8",
        )

        # Run lint_daily
        test_date = "2026-09-15"
        result = subprocess.run(
            [
                "python3",
                "scripts/lint_daily.py",
                "--vault",
                str(vault_path),
                "--date",
                test_date,
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Check report shows error
        report_path = vault_path / "_lint" / f"lint-{test_date}.md"
        report_content = report_path.read_text(encoding="utf-8")

        assert "Errors:" in report_content
        assert "Broken wikilink" in report_content or "nonexistent-note" in report_content


def test_lint_daily_logs_vault_error():
    """Test that the script logs to .memex/log.jsonl on vault error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = pathlib.Path(tmpdir) / "nonexistent-vault"

        # Run lint_daily on non-existent vault
        result = subprocess.run(
            [
                "python3",
                "scripts/lint_daily.py",
                "--vault",
                str(vault_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "ERROR:" in result.stderr

        # Check that log.jsonl was created and contains error event
        log_file = vault_path / ".memex" / "log.jsonl"
        assert log_file.exists()

        log_content = log_file.read_text(encoding="utf-8")
        assert "lint_daily_vault_error" in log_content

        # Parse JSON to verify structure
        event = json.loads(log_content.strip())
        assert event["event"] == "lint_daily_vault_error"
        assert event["level"] == "error"
        assert "timestamp" in event


def test_lint_daily_respects_gitignore_patterns():
    """Test that the script skips .memex and raw/ directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = pathlib.Path(tmpdir) / "test-vault"
        vault_path.mkdir()

        # Create notes in excluded directories
        (vault_path / ".memex").mkdir()
        (vault_path / ".memex" / "internal.md").write_text("# Internal", encoding="utf-8")

        (vault_path / "raw").mkdir()
        (vault_path / "raw" / "source.md").write_text("# Source", encoding="utf-8")

        # Create a valid note in included directory
        (vault_path / "test.md").write_text(
            """---
type: concept
title: Test
status: active
---

# Test
""",
            encoding="utf-8",
        )

        # Run lint_daily
        test_date = "2026-09-15"
        result = subprocess.run(
            [
                "python3",
                "scripts/lint_daily.py",
                "--vault",
                str(vault_path),
                "--date",
                test_date,
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Check report only counted the included note
        report_path = vault_path / "_lint" / f"lint-{test_date}.md"
        report_content = report_path.read_text(encoding="utf-8")

        assert "Scanned: 1 notes" in report_content


def test_lint_daily_max_findings_cap():
    """Test that --max-findings caps the listed findings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = pathlib.Path(tmpdir) / "test-vault"
        vault_path.mkdir()

        # Create 20 notes without frontmatter
        for i in range(20):
            (vault_path / f"bad-{i:03d}.md").write_text(
                f"# Bad Note {i}\n\nNo frontmatter.", encoding="utf-8"
            )

        # Run lint_daily with max-findings=5
        test_date = "2026-09-21"
        result = subprocess.run(
            [
                "python3",
                "scripts/lint_daily.py",
                "--vault",
                str(vault_path),
                "--date",
                test_date,
                "--max-findings",
                "5",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Check report
        report_path = vault_path / "_lint" / f"lint-{test_date}.md"
        report_content = report_path.read_text(encoding="utf-8")

        # Total count should be honest (20 errors)
        assert "Errors: 20" in report_content

        # Should show "and N more errors (omitted)"
        assert "15 more errors (omitted)" in report_content

        # Count actual listed findings (should be ≤ 5)
        listed_count = report_content.count("Missing YAML frontmatter")
        assert listed_count == 5, f"Expected 5 listed findings, got {listed_count}"


def test_lint_daily_errors_only():
    """Test that --errors-only omits warnings from listing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = pathlib.Path(tmpdir) / "test-vault"
        vault_path.mkdir()

        # Create note with error
        (vault_path / "bad.md").write_text("# Bad Note\n\nNo frontmatter.", encoding="utf-8")

        # Create orphan note in wiki/ (would be a warning)
        wiki_dir = vault_path / "wiki"
        wiki_dir.mkdir()
        (wiki_dir / "orphan.md").write_text(
            """---
type: concept
title: Orphan
status: active
---

# Orphan

No one links to this.
""",
            encoding="utf-8",
        )

        # Run lint_daily with --errors-only
        test_date = "2026-09-21"
        result = subprocess.run(
            [
                "python3",
                "scripts/lint_daily.py",
                "--vault",
                str(vault_path),
                "--date",
                test_date,
                "--errors-only",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Check report
        report_path = vault_path / "_lint" / f"lint-{test_date}.md"
        report_content = report_path.read_text(encoding="utf-8")

        # Should count both errors and warnings
        assert "Errors: 1" in report_content
        assert "Warnings: 1" in report_content

        # Should show error
        assert "Missing YAML frontmatter" in report_content

        # Should NOT show orphan warning in detail, but mention it was omitted
        assert "Orphan atomic note" not in report_content
        assert "warnings omitted (--errors-only)" in report_content


def test_lint_daily_scope_wiki():
    """Test that --scope wiki skips people/, companies/, books/."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = pathlib.Path(tmpdir) / "test-vault"
        vault_path.mkdir()

        # Create notes in different directories
        (vault_path / "wiki").mkdir()
        (vault_path / "wiki" / "concept.md").write_text(
            "---\ntype: concept\ntitle: Test\nstatus: active\n---\n\n# Test\n",
            encoding="utf-8",
        )

        (vault_path / "people").mkdir()
        (vault_path / "people" / "person.md").write_text(
            "# Bad Person\n\nNo frontmatter.", encoding="utf-8"
        )

        (vault_path / "companies").mkdir()
        (vault_path / "companies" / "company.md").write_text(
            "# Bad Company\n\nNo frontmatter.", encoding="utf-8"
        )

        # Run with scope=wiki (should skip people/, companies/)
        test_date = "2026-09-21"
        result = subprocess.run(
            [
                "python3",
                "scripts/lint_daily.py",
                "--vault",
                str(vault_path),
                "--date",
                test_date,
                "--scope",
                "wiki",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Check report
        report_path = vault_path / "_lint" / f"lint-{test_date}.md"
        report_content = report_path.read_text(encoding="utf-8")

        # Should only scan 1 note (wiki/concept.md)
        assert "Scanned: 1 notes" in report_content
        # Should have 0 errors (the wiki note is valid)
        assert "Errors: 0" in report_content


if __name__ == "__main__":
    import pytest
    import sys

    sys.exit(pytest.main([__file__, "-v"]))
