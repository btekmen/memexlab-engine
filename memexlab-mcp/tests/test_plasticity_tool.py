"""The MCP plasticity tool is read-only."""
import datetime
import hashlib

from memexlab_mcp import server
from memexlab_mcp.vault import Vault

NOW = datetime.datetime(2026, 11, 6, tzinfo=datetime.timezone.utc)


def _hash(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(root)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def test_tool_scores_without_touching_the_vault(fixture_vault, monkeypatch):
    monkeypatch.delenv("MEMEX_METER_PATH", raising=False)
    old = (NOW - datetime.timedelta(days=30)).date().isoformat()
    (fixture_vault / "concepts" / "governed-memory.md").write_text(
        f"---\ntitle: Governed Memory\nstatus: contested\ncaptured_at: '{old}T00:00:00+00:00'\n---\n"
        "Still the same claim.\n",
        encoding="utf-8",
    )
    before = _hash(fixture_vault)
    server.configure(str(fixture_vault))
    report = server.plasticity(policy="rps", limit=5)
    assert report["read_only"] is True and report["edited"] is False and report["network"] is False
    row = next(n for n in report["policies"]["rps"]["notes"] if n["slug"] == "governed-memory")
    contested = next(f for f in row["factors"] if f["factor"] == "contested")
    assert contested["value"] == 1
    assert contested["detail"]
    assert _hash(fixture_vault) == before
    assert Vault(fixture_vault).notes()
