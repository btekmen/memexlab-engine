import hashlib
import json
import pathlib

import pytest

from memexlab_mcp.governance import capture_note, write_dir
from memexlab_mcp.vault import Vault


def _tree_hash(root: pathlib.Path, exclude: set[str]) -> dict:
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if not p.is_file() or (rel.parts and rel.parts[0] in exclude):
            continue
        out[str(rel)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_write_dir_defaults_to_inbox(fixture_vault):
    assert write_dir(fixture_vault) == "inbox"


def test_write_dir_respects_governance_yml(fixture_vault):
    (fixture_vault / "governance.yml").write_text("write_dir: drafts\n", encoding="utf-8")
    assert write_dir(fixture_vault) == "drafts"


def test_capture_writes_only_inbox_with_provenance_and_log(fixture_vault):
    v = Vault(fixture_vault)
    before = _tree_hash(fixture_vault, exclude={"inbox", ".memexlab"})
    res = capture_note(v, "Meeting Insight", "Prices hold.", sources=["governed-memory"], agent="testbot")
    assert res["logged"] is True
    assert res["path"].startswith("inbox/")
    text = (fixture_vault / res["path"]).read_text(encoding="utf-8")
    assert "captured_by: testbot" in text and "governed-memory" in text
    log_lines = (fixture_vault / ".memexlab" / "log.jsonl").read_text().strip().splitlines()
    entry = json.loads(log_lines[-1])
    assert entry["action"] == "capture_note" and entry["path"] == res["path"]
    # canonical untouched — byte-for-byte
    assert _tree_hash(fixture_vault, exclude={"inbox", ".memexlab"}) == before


def test_capture_rejects_path_escape(fixture_vault):
    with pytest.raises(PermissionError):
        capture_note(Vault(fixture_vault), "../evil", "nope")


def test_two_captures_same_title_do_not_collide(fixture_vault):
    v = Vault(fixture_vault)
    a = capture_note(v, "Same Title", "one")
    b = capture_note(v, "Same Title", "two")
    assert a["path"] != b["path"]
