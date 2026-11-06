"""The resolve CLI is dry-run by default and never rewrites an existing note."""
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import resolve_contest  # noqa: E402


def _vault(tmp_path: Path) -> Path:
    note = tmp_path / "concepts"
    note.mkdir()
    (note / "sample-launch.md").write_text(
        "---\ntitle: Sample launch\n---\nThe review is 1 June 2026 in Lisbon.\n",
        encoding="utf-8",
    )
    return tmp_path


def test_dry_run_writes_nothing(tmp_path):
    vault = _vault(tmp_path)
    target = (vault / "concepts" / "sample-launch.md").read_bytes()
    code = resolve_contest.main([
        "--vault", str(vault), "capture",
        "--title", "Launch moved",
        "--body", "The review moved to July 2026.",
        "--contests", "sample-launch",
    ])
    assert code == 0
    assert not (vault / "inbox").exists()
    assert (vault / "concepts" / "sample-launch.md").read_bytes() == target


def test_apply_files_a_contested_note_without_editing_the_target(tmp_path, capsys):
    vault = _vault(tmp_path)
    target = (vault / "concepts" / "sample-launch.md").read_bytes()
    code = resolve_contest.main([
        "--vault", str(vault), "--apply", "--format", "json", "capture",
        "--title", "Launch moved",
        "--body", "The review moved to July 2026.",
        "--contests", "sample-launch",
        "--origin-ref", "conflict:launch",
    ])
    assert code == 0
    assert (vault / "concepts" / "sample-launch.md").read_bytes() == target
    filed = list((vault / "inbox").glob("*.md"))
    assert len(filed) == 1
    text = filed[0].read_text(encoding="utf-8")
    assert "status: contested" in text
    assert "sample-launch" in text
    again = resolve_contest.main([
        "--vault", str(vault), "--apply", "capture",
        "--title", "Launch moved again",
        "--body", "This body must not replace the first note.",
        "--contests", "sample-launch",
        "--origin-ref", "conflict:launch",
    ])
    assert again == 0
    assert filed[0].read_text(encoding="utf-8") == text
    assert (vault / "concepts" / "sample-launch.md").read_bytes() == target
    capsys.readouterr()


def test_apply_proposal_and_refuse_plain_note(tmp_path):
    vault = _vault(tmp_path)
    target = (vault / "concepts" / "sample-launch.md").read_bytes()
    assert resolve_contest.main([
        "--vault", str(vault), "--apply", "capture",
        "--title", "Launch moved",
        "--body", "July 2026.",
        "--contests", "sample-launch",
    ]) == 0
    contest = next((vault / "inbox").glob("*.md"))
    contest_bytes = contest.read_bytes()
    slug = contest.stem
    code = resolve_contest.main([
        "--vault", str(vault), "--apply", "propose",
        "--contest", slug,
        "--proposal", "Adopt July 2026 and leave the June note in place.",
    ])
    assert code == 0
    assert contest.read_bytes() == contest_bytes
    assert (vault / "concepts" / "sample-launch.md").read_bytes() == target
    notes = list((vault / "inbox").glob("*.md"))
    assert len(notes) == 2
    proposal = next(p for p in notes if p != contest)
    assert "resolution:" in proposal.read_text(encoding="utf-8")
    refused = resolve_contest.main([
        "--vault", str(vault), "--apply", "propose",
        "--contest", "sample-launch",
        "--proposal", "Should not file.",
    ])
    assert refused == 1
    assert (vault / "concepts" / "sample-launch.md").read_bytes() == target
    assert len(list((vault / "inbox").glob("*.md"))) == 2
