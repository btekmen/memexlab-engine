"""Conflict capture and resolution proposals leave existing notes untouched."""
import hashlib

import pytest

from memexlab_mcp.governance import capture_note, propose_resolution
from memexlab_mcp.prompt_index import build_prompt_index
from memexlab_mcp.search import search
from memexlab_mcp.vault import Vault


def _bytes(path):
    return path.read_bytes()


def test_contest_writes_a_new_note_and_leaves_the_target_unchanged(fixture_vault):
    target = fixture_vault / "concepts" / "governed-memory.md"
    before = _bytes(target)
    other = _bytes(fixture_vault / "concepts" / "harness-engineering.md")
    v = Vault(fixture_vault)
    res = capture_note(
        v, "Memory is disposable",
        "A later source says the vault may be rewritten in place.",
        contests=["governed-memory"], agent="testbot", origin_ref="conflict:1",
    )
    assert res["created"] is True
    assert res["status"] == "contested"
    assert res["contests"] == ["governed-memory"]
    assert res["path"].startswith("inbox/")
    text = (fixture_vault / res["path"]).read_text(encoding="utf-8")
    assert "status: contested" in text
    assert "governed-memory" in text
    assert "rewritten in place" in text
    assert _bytes(target) == before
    assert _bytes(fixture_vault / "concepts" / "harness-engineering.md") == other
    assert hashlib.sha256(target.read_bytes()).hexdigest() == hashlib.sha256(before).hexdigest()


def test_repeat_origin_ref_does_not_edit_the_contested_note_or_the_target(fixture_vault):
    target = fixture_vault / "concepts" / "governed-memory.md"
    v = Vault(fixture_vault)
    first = capture_note(v, "Conflict", "evidence one", contests=["governed-memory"],
                         origin_ref="conflict:same")
    filed = _bytes(fixture_vault / first["path"])
    target_bytes = _bytes(target)
    again = capture_note(v, "Conflict rewritten", "evidence two", contests=["governed-memory"],
                         origin_ref="conflict:same")
    assert again["created"] is False and again["path"] == first["path"]
    assert _bytes(fixture_vault / first["path"]) == filed
    assert _bytes(target) == target_bytes
    assert "evidence two" not in (fixture_vault / first["path"]).read_text(encoding="utf-8")


def test_missing_slug_and_bad_status_write_nothing(fixture_vault):
    v = Vault(fixture_vault)
    before = sorted(p.relative_to(fixture_vault) for p in fixture_vault.rglob("*") if p.is_file())
    with pytest.raises(ValueError, match="no note to contest"):
        capture_note(v, "Nope", "evidence", contests=["missing-slug"])
    with pytest.raises(ValueError, match="requires one or more"):
        capture_note(v, "Nope", "evidence", status="contested")
    with pytest.raises(ValueError, match="needs the conflicting evidence"):
        capture_note(v, "Nope", "  ", contests=["governed-memory"])
    after = sorted(p.relative_to(fixture_vault) for p in fixture_vault.rglob("*") if p.is_file())
    assert after == before


def test_lifecycle_status_on_a_new_note_does_not_touch_existing_bytes(fixture_vault):
    target = fixture_vault / "sources" / "as-we-may-think.md"
    before = _bytes(target)
    res = capture_note(Vault(fixture_vault), "Still current", "The trails note stands.",
                       status="active")
    text = (fixture_vault / res["path"]).read_text(encoding="utf-8")
    assert "status: active" in text
    assert _bytes(target) == before
    stale = capture_note(Vault(fixture_vault), "Old claim", "Superseded by the trails note.",
                         status="stale")
    archived = capture_note(Vault(fixture_vault), "Retired claim", "Kept for the record.",
                            status="archived")
    assert "status: stale" in (fixture_vault / stale["path"]).read_text(encoding="utf-8")
    assert "status: archived" in (fixture_vault / archived["path"]).read_text(encoding="utf-8")
    assert _bytes(target) == before


def test_plain_capture_still_uses_the_write_dir_as_status(fixture_vault):
    res = capture_note(Vault(fixture_vault), "Ordinary", "no conflict")
    text = (fixture_vault / res["path"]).read_text(encoding="utf-8")
    assert "status: inbox" in text
    assert "contests:" not in text


def test_propose_resolution_files_a_proposal_and_edits_nothing(fixture_vault):
    target = fixture_vault / "concepts" / "governed-memory.md"
    target_before = _bytes(target)
    v = Vault(fixture_vault)
    filed = capture_note(v, "Conflict", "The harness is optional.", contests=["governed-memory"],
                         origin_ref="conflict:prop")
    contest_before = _bytes(fixture_vault / filed["path"])
    slug = filed["path"].split("/")[-1][:-3]
    proposal = propose_resolution(v, slug, "Keep the harness required.", origin_ref="resolve:1")
    assert proposal["created"] is True
    assert proposal["resolution"] == "proposed"
    assert proposal["resolves"] == slug
    assert proposal["status"] == "active"
    assert proposal["path"].startswith("inbox/")
    assert proposal["path"] != filed["path"]
    text = (fixture_vault / proposal["path"]).read_text(encoding="utf-8")
    assert "resolution: proposed" in text or 'resolution: "proposed"' in text
    assert "does not edit" in text
    assert "[[governed-memory]]" in text
    assert _bytes(target) == target_before
    assert _bytes(fixture_vault / filed["path"]) == contest_before
    again = propose_resolution(v, slug, "A different outcome that must not land.",
                               origin_ref="resolve:1")
    assert again["created"] is False and again["path"] == proposal["path"]
    assert "different outcome" not in (fixture_vault / proposal["path"]).read_text(encoding="utf-8")
    assert _bytes(target) == target_before


def test_propose_refuses_a_note_that_is_not_contested(fixture_vault):
    before = sorted(p.name for p in fixture_vault.rglob("*.md"))
    with pytest.raises(ValueError, match="not status contested"):
        propose_resolution(Vault(fixture_vault), "governed-memory", "No change.")
    assert sorted(p.name for p in fixture_vault.rglob("*.md")) == before


def test_index_and_search_surface_contested_notes(fixture_vault):
    v = Vault(fixture_vault)
    capture_note(v, "Conflict", "evidence about governed memory", contests=["governed-memory"])
    idx = build_prompt_index(v)
    first = idx["prompt"].splitlines()[0]
    assert "contested" in first
    assert "[[governed-memory]]" in first
    assert idx["notes"][0]["status"] == "contested"
    assert idx["notes"][0]["contests"] == ["governed-memory"]
    # a note with no status is still indexed
    assert any(n["status"] == "" for n in idx["notes"])
    hits = search(v, "governed memory evidence")
    contested = next(h for h in hits if h["status"] == "contested")
    assert contested["contests"] == ["governed-memory"]
    plain = next(h for h in hits if h["slug"] == "governed-memory")
    assert plain["status"] == ""
    assert "contests" not in plain
