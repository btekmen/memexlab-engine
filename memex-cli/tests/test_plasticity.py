"""Plasticity scores are deterministic, explainable, and read-only."""
import copy
import datetime
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from memex_cli.plasticity import DEFAULTS, load_policy, score_plasticity
from memex_cli.vault import Vault

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime.datetime(2026, 11, 6, tzinfo=datetime.timezone.utc)


def _tree(root: Path) -> dict:
    out = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def _note(folder: Path, name: str, front: str, body: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(f"---\n{front}\n---\n{body}\n", encoding="utf-8")


def _vault(tmp_path: Path) -> Vault:
    old = (NOW - datetime.timedelta(days=30)).isoformat()
    fresh = NOW.isoformat()
    _note(
        tmp_path / "concepts", "old-conflict.md",
        f"title: Old conflict\nstatus: contested\ncaptured_at: '{old}'",
        " ".join(f"[[link-{i}]]" for i in range(5)),
    )
    _note(
        tmp_path / "concepts", "fresh.md",
        f"title: Fresh\ncaptured_at: '{fresh}'",
        "Nothing to resurface.",
    )
    _note(
        tmp_path / "inbox", "worth-keeping.md",
        f"title: Worth keeping\nstatus: active\ncaptured_at: '{fresh}'\n"
        "sources: [old-conflict]\norigin_ref: 'src:1'",
        "A substantial inbox note that cites [[old-conflict]]. " + ("word " * 80),
    )
    _note(
        tmp_path / "inbox", "conflict-copy.md",
        f"title: Conflict copy\nstatus: contested\ncaptured_at: '{fresh}'",
        "short",
    )
    meter = tmp_path / ".memex"
    meter.mkdir()
    record = {
        "v": 1, "ts": NOW.isoformat(), "route": "memex.search",
        "retrieved_tokens": 4, "cited_slugs": ["old-conflict"], "hit": True,
    }
    miss = dict(record, hit=False, cited_slugs=["fresh"])
    lines = "\n".join(json.dumps(record) for _ in range(3))
    (meter / "meter.jsonl").write_text(lines + "\n" + json.dumps(miss) + "\n", encoding="utf-8")
    return Vault(tmp_path)


def test_defaults_file_matches_the_code():
    loaded = yaml.safe_load((ROOT / "schemas" / "plasticity.defaults.yml").read_text(encoding="utf-8"))
    assert loaded == DEFAULTS


def test_modules_stay_in_lockstep():
    cli = (ROOT / "memex-cli/src/memex_cli/plasticity.py").read_bytes()
    mcp = (ROOT / "memexlab-mcp/src/memexlab_mcp/plasticity.py").read_bytes()
    assert cli == mcp


def test_rps_breakdown_is_deterministic_and_ranks_the_open_conflict(tmp_path, monkeypatch):
    monkeypatch.delenv("MEMEX_METER_PATH", raising=False)
    vault = _vault(tmp_path)
    before = _tree(tmp_path)
    report = score_plasticity(vault, "rps", now=NOW)
    again = score_plasticity(vault, "rps", now=NOW)
    assert report == again
    assert report["edited"] is False and report["moved"] is False and report["network"] is False
    assert report["weights_from"] == "defaults"
    assert _tree(tmp_path) == before
    notes = report["policies"]["rps"]["notes"]
    top = notes[0]
    assert top["slug"] == "old-conflict"
    by = {f["factor"]: f for f in top["factors"]}
    assert by["recency"]["value"] == 1
    assert by["contested"]["value"] == 1
    assert by["unresolved"]["value"] == 0
    assert by["links"]["value"] == 1
    assert by["meter_hits"]["value"] == 1
    assert top["score"] == 0.8
    assert top["recommend"] is True
    assert top["open_loop"] is True
    fresh = next(row for row in notes if row["slug"] == "fresh")
    fresh_factors = {f["factor"]: f for f in fresh["factors"]}
    assert fresh_factors["recency"]["value"] == 0
    assert fresh_factors["meter_hits"]["value"] == 0
    assert fresh["score"] == 0
    assert [row["slug"] for row in notes].index("old-conflict") < [row["slug"] for row in notes].index("fresh")


def test_vault_yaml_overrides_one_weight_and_leaves_the_rest(tmp_path, monkeypatch):
    monkeypatch.delenv("MEMEX_METER_PATH", raising=False)
    vault = _vault(tmp_path)
    before_defaults = copy.deepcopy(DEFAULTS)
    (tmp_path / "plasticity.yml").write_text(
        "rps:\n  weights:\n    recency: 0\n    contested: 2\n    unresolved: 0\n    links: 0\n    meter_hits: 0\n",
        encoding="utf-8",
    )
    loaded, source = load_policy(tmp_path)
    assert source == "vault"
    assert loaded["rps"]["weights"]["contested"] == 2
    assert loaded["rps"]["recency_horizon_days"] == 30
    assert loaded["mws"] == DEFAULTS["mws"]
    assert DEFAULTS == before_defaults
    report = score_plasticity(vault, "rps", now=NOW)
    top = report["policies"]["rps"]["notes"][0]
    assert top["slug"] == "old-conflict"
    assert top["score"] == 1
    contested = next(f for f in top["factors"] if f["factor"] == "contested")
    assert contested["weight"] == 2 and contested["contribution"] == 2
    recency = next(f for f in top["factors"] if f["factor"] == "recency")
    assert recency["weight"] == 0 and recency["contribution"] == 0


def test_unknown_weight_is_refused(tmp_path):
    (tmp_path / "plasticity.yml").write_text("rps:\n  weights:\n    magic: 5\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown plasticity key"):
        load_policy(tmp_path)


def test_mws_recommends_without_moving_the_inbox_note(tmp_path, monkeypatch):
    monkeypatch.delenv("MEMEX_METER_PATH", raising=False)
    vault = _vault(tmp_path)
    before = _tree(tmp_path)
    report = score_plasticity(vault, "mws", now=NOW)
    assert _tree(tmp_path) == before
    slugs = [row["slug"] for row in report["policies"]["mws"]["notes"]]
    assert slugs == ["worth-keeping", "conflict-copy"]
    assert "old-conflict" not in slugs
    worth = report["policies"]["mws"]["notes"][0]
    factors = {f["factor"]: f for f in worth["factors"]}
    assert factors["provenance"]["value"] == 1
    assert factors["not_contested"]["value"] == 1
    assert factors["not_proposal"]["value"] == 1
    assert factors["links"]["value"] == pytest.approx(1 / 3)
    assert factors["substance"]["value"] == 1
    assert worth["recommend"] is True
    assert (tmp_path / "inbox" / "worth-keeping.md").is_file()
    assert not (tmp_path / "concepts" / "worth-keeping.md").exists()
    conflict = report["policies"]["mws"]["notes"][1]
    assert conflict["recommend"] is False
    assert next(f for f in conflict["factors"] if f["factor"] == "not_contested")["value"] == 0


def test_cli_prints_the_breakdown(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("MEMEX_METER_PATH", raising=False)
    _vault(tmp_path)
    from memex_cli.cli import main
    code = main(["plasticity", "rps", "--vault", str(tmp_path), "--format", "json"])
    out, err = capsys.readouterr()
    assert code == 0
    report = json.loads(out)
    assert report["policies"]["rps"]["notes"][0]["score"] == 0.8
    event = json.loads(err.strip().splitlines()[-1])
    assert event["cmd"] == "plasticity" and event["ok"] and event["read_only"]
