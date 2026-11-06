import ast
import json
import pathlib

import pytest

from memexlab_mcp import server
from memexlab_mcp.meter import estimate_tokens, record, resolve_path, summarize


def test_estimate_tokens_is_utf8_bytes_over_four():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcde") == 2
    assert estimate_tokens("é") == 1  # c3 a9 — 2 bytes → 1 token


def test_record_format_leaves_hit_null(tmp_path, monkeypatch):
    monkeypatch.delenv("MEMEX_METER_PATH", raising=False)
    vault = tmp_path / "vault"
    vault.mkdir()
    rec = record(vault, route="mcp.search_vault", text="abcd", cited_slugs=["ada", "ada"],
                 query="governed\nmemory")
    assert rec["written"] is True
    assert rec["retrieved_tokens"] == 1
    assert rec["hit"] is None
    assert rec["cited_slugs"] == ["ada"]
    line = json.loads((vault / ".memex" / "meter.jsonl").read_text(encoding="utf-8"))
    for key in ("v", "ts", "route", "retrieved_tokens", "cited_slugs", "hit"):
        assert key in line
    assert line["v"] == 1
    assert line["route"] == "mcp.search_vault"
    assert line["retrieved_tokens"] == 1
    assert line["cited_slugs"] == ["ada"]
    assert line["hit"] is None
    assert line["query"] == "governed memory"
    assert "written" not in line
    assert "body" not in line


def test_meter_module_imports_no_network_stack():
    src = pathlib.Path(record.__code__.co_filename).read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint({"urllib", "socket", "http", "requests"})


def test_summary_counts_pending_until_eval_fills_hit(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    path = vault / "meter.jsonl"
    record(vault, route="mcp.read_note", text="abcdefgh", cited_slugs=["ada"], path=path)
    record(vault, route="memex.qa", text="", cited_slugs=["ada", "bush"], path=path)
    # An eval may later set hit. The writer never does; the summary must count it.
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "v": 1, "ts": "t", "route": "memex.qa", "retrieved_tokens": 4,
            "cited_slugs": ["ada"], "hit": True,
        }) + "\n")
        handle.write(json.dumps({
            "v": 1, "ts": "t", "route": "memex.search", "retrieved_tokens": 0,
            "cited_slugs": [], "hit": False,
        }) + "\n")
        handle.write("not json\n")
    summary = summarize(path)
    assert summary["records"] == 4
    assert summary["skipped"] == 1
    assert summary["pending"] == 2
    assert summary["hit"] == 1
    assert summary["miss"] == 1
    assert summary["retrieved_tokens"] == 2 + 0 + 4 + 0
    assert summary["cited_slugs"]["ada"] == 3
    assert summary["by_route"]["mcp.read_note"]["records"] == 1


def test_path_override_env_and_governance(tmp_path, monkeypatch):
    monkeypatch.delenv("MEMEX_METER_PATH", raising=False)
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "governance.yml").write_text("meter_path: local/meter.jsonl\n", encoding="utf-8")
    record(vault, route="mcp.get_index", text="ab", cited_slugs=[])
    assert (vault / "local" / "meter.jsonl").is_file()
    assert not (vault / ".memex" / "meter.jsonl").exists()

    monkeypatch.setenv("MEMEX_METER_PATH", str(tmp_path / "env.jsonl"))
    record(vault, route="mcp.get_index", text="abcd", cited_slugs=["s"])
    assert (tmp_path / "env.jsonl").is_file()

    with pytest.raises(PermissionError):
        resolve_path(vault, "../outside.jsonl")
    with pytest.raises(ValueError):
        resolve_path(vault, "https://example.com/meter.jsonl")


def test_server_retrieval_writes_meter_and_index_has_no_body(fixture_vault, monkeypatch):
    monkeypatch.delenv("MEMEX_METER_PATH", raising=False)
    server.configure(str(fixture_vault))
    idx = server.get_index()
    assert idx["count"] == 3
    assert "[[governed-memory]]" in idx["prompt"]
    assert "durable, citable and auditable" not in idx["prompt"]
    hits = server.search_vault("governed memory")
    note = server.read_note("governed-memory")
    assert note["path"] == "concepts/governed-memory.md"
    lines = (fixture_vault / ".memex" / "meter.jsonl").read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    routes = [r["route"] for r in records]
    assert routes == ["mcp.get_index", "mcp.search_vault", "mcp.read_note"]
    for rec in records:
        assert rec["hit"] is None
        assert isinstance(rec["retrieved_tokens"], int)
        assert isinstance(rec["cited_slugs"], list)
        assert "governed-memory" in rec["cited_slugs"]
    assert records[1]["cited_slugs"][0] == hits[0]["slug"]
    # a bad meter path must not break retrieval
    monkeypatch.setenv("MEMEX_METER_PATH", "../nope.jsonl")
    again = server.search_vault("governed memory")
    assert again[0]["slug"] == "governed-memory"
