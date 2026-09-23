"""Tests for the three first-class CLI gestures: save, ask, approve."""
from __future__ import annotations

import pathlib
import tempfile
from unittest.mock import patch

import pytest

from memex_cli import governance, queue
from memex_cli.vault import Vault


@pytest.fixture
def vault(tmp_path: pathlib.Path) -> Vault:
    (tmp_path / "wiki").mkdir()
    (tmp_path / "wiki" / "test.md").write_text(
        "---\ntitle: Test Note\n---\n\nThis is a test note about [[platform-banking]].",
        encoding="utf-8"
    )
    (tmp_path / "inbox").mkdir()
    (tmp_path / "queue").mkdir()
    return Vault(str(tmp_path))


def test_save_dry_run(vault: Vault) -> None:
    before = list((vault.root / "inbox").glob("*.md"))
    title = "Test Save"
    body = "This is a test save."
    
    slug = governance._slugify(title)
    wd = governance.write_dir(vault.root)
    
    assert slug == "test-save"
    assert wd == "inbox"
    assert len(before) == 0


def test_save_apply_lands_in_inbox_only(vault: Vault) -> None:
    title = "Test Save"
    body = "This is a test save with some content."
    
    result = governance.capture_note(vault, title, body, sources=["test"])
    
    assert result["logged"] is True
    assert "path" in result
    path = pathlib.Path(result["path"])
    assert path.parts[0] == "inbox"
    
    written = vault.root / result["path"]
    assert written.exists()
    content = written.read_text(encoding="utf-8")
    assert "title: Test Save" in content
    assert "captured_by: memex-cli" in content
    assert "sources:" in content
    assert "- test" in content
    assert "This is a test save with some content." in content
    
    wiki_files = list((vault.root / "wiki").glob("*.md"))
    assert all("test-save" not in f.stem for f in wiki_files)


def test_ask_returns_without_writing_canonical(vault: Vault, tmp_path: pathlib.Path) -> None:
    (tmp_path / "wiki" / "platform.md").write_text(
        "---\ntitle: Platform Banking\n---\n\nPlatform banking is a modern approach.",
        encoding="utf-8"
    )
    
    wiki_before = {f.name: f.read_text(encoding="utf-8") 
                   for f in (vault.root / "wiki").glob("*.md")}
    
    from memex_cli.search import search
    hits = search(vault, "platform banking", limit=3)
    
    assert len(hits) >= 0
    
    wiki_after = {f.name: f.read_text(encoding="utf-8") 
                  for f in (vault.root / "wiki").glob("*.md")}
    assert wiki_before == wiki_after


def test_ask_works_without_writing_canonical(vault: Vault) -> None:
    from memex_cli.qa import qa
    
    wiki_before = {f.name: f.read_text(encoding="utf-8") 
                   for f in (vault.root / "wiki").glob("*.md")}
    
    fake_provider = {"kind": "openai", "url": "http://fake", "key": "", "model": "test", "route": "test"}
    def fake_complete(prov, system, question, max_tokens=1000):
        return {"text": "Platform banking [[test]] is mentioned.", "model": "test", "usage": {}}
    
    result = qa(vault, "what is platform banking", apply=False, 
                provider=fake_provider, complete=fake_complete)
    
    assert result["action"] == "qa"
    assert result["ok"] is True
    assert "answer" in result
    
    wiki_after = {f.name: f.read_text(encoding="utf-8") 
                  for f in (vault.root / "wiki").glob("*.md")}
    assert wiki_before == wiki_after


def test_approve_list(vault: Vault) -> None:
    (vault.root / "queue" / "task1.md").write_text(
        "---\ntype: queue-item\ntitle: Task 1\nstatus: pending\ncreated: 2026-01-01\n---\n\nDo something.",
        encoding="utf-8"
    )
    (vault.root / "queue" / "task2.md").write_text(
        "---\ntype: queue-item\ntitle: Task 2\nstatus: done\ncreated: 2026-01-02\n---\n\nAlready done.",
        encoding="utf-8"
    )
    
    items = queue.list_queue(vault, status="pending")
    assert len(items) == 1
    assert items[0]["item"] == "task1"
    assert items[0]["status"] == "pending"


def test_approve_complete_does_not_touch_wiki(vault: Vault) -> None:
    (vault.root / "queue" / "task1.md").write_text(
        "---\ntype: queue-item\ntitle: Task 1\nstatus: pending\ncreated: 2026-01-01\n---\n\nDo something.",
        encoding="utf-8"
    )
    
    wiki_before = {f.name: f.read_text(encoding="utf-8") 
                   for f in (vault.root / "wiki").glob("*.md")}
    
    result = queue.complete_queue_item(
        vault, "task1", "Task 1 Result", "This is the result of task 1."
    )
    
    assert result["status"] == "done"
    assert "result" in result
    result_path = pathlib.Path(result["result"])
    assert result_path.parts[0] == "inbox"
    
    wiki_after = {f.name: f.read_text(encoding="utf-8") 
                  for f in (vault.root / "wiki").glob("*.md")}
    assert wiki_before == wiki_after
    
    queue_item = vault.root / "queue" / "task1.md"
    content = queue_item.read_text(encoding="utf-8")
    assert "status: done" in content
    assert result["result"] in content


def test_approve_drop(vault: Vault) -> None:
    (vault.root / "queue" / "task1.md").write_text(
        "---\ntype: queue-item\ntitle: Task 1\nstatus: pending\ncreated: 2026-01-01\n---\n\nDo something.",
        encoding="utf-8"
    )
    
    result = queue.drop_queue_item(vault, "task1")
    
    assert result["status"] == "cancelled"
    assert result["logged"] is True
    
    queue_item = vault.root / "queue" / "task1.md"
    content = queue_item.read_text(encoding="utf-8")
    assert "status: cancelled" in content


def test_save_governance_boundary(vault: Vault) -> None:
    with pytest.raises(PermissionError, match="path separators"):
        governance.capture_note(vault, "../escape", "bad")
    
    with pytest.raises(PermissionError, match="path separators"):
        governance.capture_note(vault, "sub/path", "bad")


def test_queue_item_not_found(vault: Vault) -> None:
    with pytest.raises(ValueError, match="no queue item named"):
        queue.complete_queue_item(vault, "nonexistent", "Title", "Body")


def test_queue_complete_requires_result(vault: Vault) -> None:
    (vault.root / "queue" / "task1.md").write_text(
        "---\ntype: queue-item\ntitle: Task 1\nstatus: pending\n---\n\nDo something.",
        encoding="utf-8"
    )
    
    with pytest.raises(ValueError, match="non-empty result"):
        queue.complete_queue_item(vault, "task1", "", "Body")
    
    with pytest.raises(ValueError, match="non-empty result"):
        queue.complete_queue_item(vault, "task1", "Title", "")
