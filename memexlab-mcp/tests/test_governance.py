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


def test_write_dir_tolerates_non_mapping_governance_yml(fixture_vault):
    (fixture_vault / "governance.yml").write_text("- one\n- two\n", encoding="utf-8")
    assert write_dir(fixture_vault) == "inbox"
    (fixture_vault / "governance.yml").write_text("just-a-string\n", encoding="utf-8")
    assert write_dir(fixture_vault) == "inbox"


def test_capture_writes_markdown_only_inside_inbox(fixture_vault):
    v = Vault(fixture_vault)
    before = {p.relative_to(fixture_vault) for p in fixture_vault.rglob("*") if p.is_file()}
    res = capture_note(v, "Only Inbox", "lands in the inbox", origin_ref="src:inbox-only")
    after = {p.relative_to(fixture_vault) for p in fixture_vault.rglob("*") if p.is_file()}
    new_md = [p for p in after - before if p.suffix == ".md"]
    assert res["created"] is True
    assert res["path"].startswith("inbox/")
    assert new_md == [pathlib.Path(res["path"])]
    text = (fixture_vault / res["path"]).read_text(encoding="utf-8")
    assert "origin_ref:" in text and "src:inbox-only" in text


def test_origin_ref_is_idempotent_and_does_not_edit(fixture_vault):
    v = Vault(fixture_vault)
    first = capture_note(v, "First title", "original body", origin_ref="src:chat:1")
    path = fixture_vault / first["path"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    inbox_before = sorted(p.name for p in (fixture_vault / "inbox").glob("*.md"))
    canonical = (fixture_vault / "concepts" / "governed-memory.md").read_bytes()
    second = capture_note(
        v, "Different title", "different body that must not land",
        origin_ref="src:chat:1",
    )
    assert second["created"] is False and second["idempotent"] is True
    assert second["path"] == first["path"]
    assert second["note"]["path"] == first["path"]
    assert "original body" in second["note"]["body"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    assert "different body" not in path.read_text(encoding="utf-8")
    assert sorted(p.name for p in (fixture_vault / "inbox").glob("*.md")) == inbox_before
    assert (fixture_vault / "concepts" / "governed-memory.md").read_bytes() == canonical
    log = (fixture_vault / ".memexlab" / "log.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(log[-1])["action"] == "capture_note_idempotent"


def test_origin_ref_on_existing_note_does_not_duplicate_or_edit(fixture_vault):
    note = fixture_vault / "concepts" / "governed-memory.md"
    original = note.read_text(encoding="utf-8")
    if original.startswith("---\n"):
        seeded = original.replace("---\n", "---\norigin_ref: already-there\n", 1)
    else:
        seeded = "---\norigin_ref: already-there\n---\n" + original
    note.write_text(seeded, encoding="utf-8")
    digest = note.read_bytes()
    res = capture_note(Vault(fixture_vault), "New", "new body", origin_ref="already-there")
    assert res["created"] is False
    assert res["path"] == "concepts/governed-memory.md"
    assert note.read_bytes() == digest
    assert not (fixture_vault / "inbox").exists()


def test_origin_ref_round_trips_yaml_scalars(fixture_vault):
    v = Vault(fixture_vault)
    samples = ["yes", "no", "true", "null", "123", "2026-11-06", 'say "hi"', "it's",
               "chat:turn:1"]
    for ref in samples:
        res = capture_note(v, f"Note {ref}", "body", origin_ref=ref)
        again = capture_note(v, "retry", "other", origin_ref=ref)
        assert again["created"] is False and again["path"] == res["path"]
        assert again["note"]["frontmatter"]["origin_ref"] == ref


def test_blank_origin_ref_does_not_collapse_captures(fixture_vault):
    v = Vault(fixture_vault)
    a = capture_note(v, "Blank", "one", origin_ref="  ")
    b = capture_note(v, "Blank", "two", origin_ref="")
    assert a["created"] and b["created"] and a["path"] != b["path"]
    assert "origin_ref" not in (fixture_vault / a["path"]).read_text(encoding="utf-8")


def test_origin_ref_rejects_newlines(fixture_vault):
    with pytest.raises(ValueError):
        capture_note(Vault(fixture_vault), "Bad", "body", origin_ref="one\ntwo")


def test_capture_long_title_is_bounded_and_succeeds(fixture_vault):
    v = Vault(fixture_vault)
    res = capture_note(v, "T" * 500, "long title body")
    assert res["logged"] is True and res["path"].startswith("inbox/")
    name = pathlib.Path(res["path"]).name
    assert len(name.encode("utf-8")) <= 120
