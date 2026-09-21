"""Containment tests for runner/tools.py — the agent's only door to the vault.

These cover the three boundaries the Workspace is supposed to hold:
writes confined to the governance write dir (and never clobbering), globs that
cannot escape the root, and search that refuses to follow symlinks out.
"""
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "runner"))

from tools import Workspace  # noqa: E402


@pytest.fixture
def vault(tmp_path):
    root = tmp_path / "vault"
    (root / "inbox").mkdir(parents=True)
    (root / "people").mkdir()
    (root / "people" / "ada.md").write_text(
        "---\ntype: person\n---\n\nAda's canonical note.\n", encoding="utf-8")
    return root


@pytest.fixture
def outside(tmp_path):
    out = tmp_path / "outside"
    out.mkdir()
    (out / "secrets.md").write_text(
        "---\ntype: note\n---\n\nboard minutes: the number is 42\n", encoding="utf-8")
    return out


# --- FIX 1: write containment -------------------------------------------------

def test_write_file_allows_the_write_dir(vault):
    ws = Workspace(vault)
    ws.write_file("inbox/capture.md", "---\ntype: note\n---\n\nhello\n")
    assert (vault / "inbox" / "capture.md").is_file()


def test_write_file_refuses_canonical_paths(vault):
    ws = Workspace(vault)
    with pytest.raises(PermissionError):
        ws.write_file("people/ada.md", "blanked")
    assert "canonical" in (vault / "people" / "ada.md").read_text(encoding="utf-8")


def test_write_file_refuses_new_file_outside_write_dir(vault):
    ws = Workspace(vault)
    with pytest.raises(PermissionError):
        ws.write_file("people/new-person.md", "---\ntype: person\n---\n")
    assert not (vault / "people" / "new-person.md").exists()


def test_write_file_refuses_overwrite_inside_write_dir(vault):
    ws = Workspace(vault)
    ws.write_file("inbox/note.md", "first")
    with pytest.raises(PermissionError):
        ws.write_file("inbox/note.md", "second")
    assert (vault / "inbox" / "note.md").read_text(encoding="utf-8") == "first"


def test_write_file_refuses_escape_via_symlinked_write_dir(vault, outside):
    (vault / "inbox" / "elsewhere").symlink_to(outside, target_is_directory=True)
    ws = Workspace(vault)
    with pytest.raises((PermissionError, ValueError)):
        ws.write_file("inbox/elsewhere/planted.md", "x")
    assert not (outside / "planted.md").exists()


def test_write_file_honours_governance_write_dir(vault):
    yaml = pytest.importorskip("yaml")
    (vault / "governance.yml").write_text(
        yaml.safe_dump({"write_dir": "capture"}), encoding="utf-8")
    ws = Workspace(vault)
    ws.write_file("capture/note.md", "ok")
    assert (vault / "capture" / "note.md").is_file()
    with pytest.raises(PermissionError):
        ws.write_file("inbox/note.md", "nope")


def test_write_file_appends_an_audit_entry(vault):
    ws = Workspace(vault)
    ws.write_file("inbox/logged.md", "body")
    log = vault / ".memexlab" / "log.jsonl"
    assert log.is_file(), "governance.yml promises writes are logged"
    entry = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
    assert entry["action"] == "write_file"
    assert entry["path"] == "inbox/logged.md"
    assert entry["ts"]


# --- FIX 2: glob containment --------------------------------------------------

def test_list_files_rejects_parent_traversal_glob(vault, outside):
    ws = Workspace(vault)
    with pytest.raises(ValueError):
        ws.list_files("../outside/*.md")


def test_list_files_rejects_deep_parent_traversal_glob(vault):
    ws = Workspace(vault)
    with pytest.raises(ValueError):
        ws.list_files("../../*.md")


def test_list_files_rejects_absolute_glob(vault):
    ws = Workspace(vault)
    with pytest.raises(ValueError):
        ws.list_files("/etc/*")


def test_list_files_rejects_empty_glob(vault):
    ws = Workspace(vault)
    with pytest.raises(ValueError):
        ws.list_files("")


def test_list_files_skips_symlinked_escape(vault, outside):
    (vault / "linked").symlink_to(outside, target_is_directory=True)
    ws = Workspace(vault)
    assert all("secrets" not in f for f in ws.list_files())


def test_list_files_skips_symlinked_file_escape(vault, outside):
    (vault / "leak.md").symlink_to(outside / "secrets.md")
    ws = Workspace(vault)
    assert "leak.md" not in ws.list_files()


def test_list_files_still_lists_real_vault_files(vault):
    ws = Workspace(vault)
    assert ws.list_files() == ["people/ada.md"]


# --- FIX 3: search containment ------------------------------------------------

def test_search_does_not_leak_through_symlinked_dir(vault, outside):
    (vault / "linked").symlink_to(outside, target_is_directory=True)
    ws = Workspace(vault)
    assert ws.search("board minutes") == []


def test_search_does_not_leak_through_symlinked_file(vault, outside):
    (vault / "leak.md").symlink_to(outside / "secrets.md")
    ws = Workspace(vault)
    assert ws.search("board minutes") == []


def test_search_still_finds_vault_content(vault):
    ws = Workspace(vault)
    hits = ws.search("canonical")
    assert len(hits) == 1 and hits[0].startswith("people/ada.md:")


def test_module_docstring_does_not_overclaim():
    import tools
    assert "Every path is resolved against the vault root" not in tools.__doc__
