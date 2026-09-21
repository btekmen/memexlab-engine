"""Tests for the publication gate declared in governance.yml.

governance.yml's release_policy names scripts/readiness_check.py as a required
check before public release, and deny_publication_patterns names the categories
it has to catch. These tests keep that control honest: they plant one concrete
instance of each machine-detectable category and assert the scan flags it.
"""
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent
REPO = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import readiness_check  # noqa: E402


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "clean.md").write_text(
        "# Docs\n\nMail us at hello@example.com.\n", encoding="utf-8")
    return tmp_path


def plant(tree, name, body):
    (tree / "docs" / name).write_text(body, encoding="utf-8")
    return readiness_check.scan(tree)


def test_clean_tree_has_no_findings(tree):
    assert readiness_check.scan(tree) == []


def test_flags_credentials(tree):
    errors = plant(tree, "leak.md", "aws key AKIA" + "ABCDEFGHIJKLMNOP\n")
    assert any("AWS access key" in e for e in errors)


def test_flags_private_key_block(tree):
    errors = plant(tree, "leak.md", "-----BEGIN RSA " + "PRIVATE KEY-----\nxx\n")
    assert any("private key block" in e for e in errors)


def test_flags_personal_contact_details(tree):
    errors = plant(tree, "board.md", "Chair: ada.stone" + "@acmebank" + ".co.uk\n")
    assert any("personal contact detail" in e for e in errors)


def test_allows_placeholder_addresses(tree):
    errors = plant(tree, "sample.md", "someone@example.org and me@yourorg\n")
    assert errors == []


def test_flags_unscrubbed_vault_markers(tree):
    errors = plant(tree, "note.md", "owner: TODO_" + "REAL_NAME\n")
    assert any("unscrubbed marker" in e for e in errors)


def test_skips_ignored_dirs_and_binary_suffixes(tree):
    (tree / ".git").mkdir()
    (tree / ".git" / "config.md").write_text(
        "AKIA" + "ABCDEFGHIJKLMNOP\n", encoding="utf-8")
    (tree / "docs" / "image.png").write_bytes(b"AKIA" + b"ABCDEFGHIJKLMNOP")
    assert readiness_check.scan(tree) == []


def test_repo_passes_the_declared_gate():
    """The gate governance.yml declares must actually be green on this repo."""
    r = subprocess.run([sys.executable, "scripts/readiness_check.py"],
                       cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
