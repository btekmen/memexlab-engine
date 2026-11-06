import json
import pathlib
import subprocess
import sys

import pytest

from memex_cli import cli
from memex_cli.meter import record, summarize
from memex_cli.qa import qa
from memex_cli.vault import Vault

FAKE_PROVIDER = {"kind": "openai", "url": "http://local", "key": "",
                 "model": "test-model", "route": "local"}
REPO = pathlib.Path(__file__).resolve().parents[2]


@pytest.fixture
def vault(tmp_path: pathlib.Path) -> Vault:
    (tmp_path / "concepts").mkdir()
    (tmp_path / "concepts" / "governed-memory.md").write_text(
        "---\ntitle: Governed Memory\n---\n"
        "Governed memory keeps agent knowledge durable and citable.\n",
        encoding="utf-8",
    )
    return Vault(tmp_path)


def _fake_complete(answer: str):
    def complete(provider, system, user, max_tokens=1000):
        return {"text": answer, "model": provider["model"], "usage": {"input": 1, "output": 1}}
    return complete


def test_search_and_qa_write_meter_records(vault, monkeypatch, capsys):
    monkeypatch.delenv("MEMEX_METER_PATH", raising=False)
    assert cli.main(["search", "governed", "--vault", str(vault.root)]) == 0
    capsys.readouterr()
    res = qa(vault, "what is governed memory", provider=FAKE_PROVIDER,
             complete=_fake_complete("It is durable [[governed-memory]]."))
    assert res["ok"]
    qa(vault, "no such topic zzzqqq", provider=FAKE_PROVIDER, complete=_fake_complete("x"))
    lines = (vault.root / ".memex" / "meter.jsonl").read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    assert [r["route"] for r in records] == ["memex.search", "memex.qa", "memex.qa"]
    for rec in records:
        assert rec["v"] == 1
        assert rec["hit"] is None
        assert isinstance(rec["retrieved_tokens"], int) and rec["retrieved_tokens"] >= 0
        assert isinstance(rec["cited_slugs"], list)
    assert records[0]["cited_slugs"] == ["governed-memory"]
    assert records[0]["retrieved_tokens"] > 0
    assert records[1]["cited_slugs"] == ["governed-memory"]
    assert records[1]["retrieved_tokens"] > 0
    assert records[2]["cited_slugs"] == []
    assert records[2]["retrieved_tokens"] == 0


def test_memex_meter_summarizes_pending_hits(vault, capsys, monkeypatch):
    monkeypatch.delenv("MEMEX_METER_PATH", raising=False)
    record(vault.root, route="memex.search", text="abcd", cited_slugs=["governed-memory"],
           query="governed")
    code = cli.main(["meter", "--vault", str(vault.root), "--format", "json"])
    out, err = capsys.readouterr()
    assert code == 0
    summary = json.loads(out)
    assert summary["records"] == 1
    assert summary["pending"] == 1
    assert summary["hit"] == 0 and summary["miss"] == 0
    assert summary["retrieved_tokens"] == 1
    assert summary["cited_slugs"]["governed-memory"] == 1
    event = json.loads(err.strip().splitlines()[-1])
    assert event["cmd"] == "meter" and event["ok"] is True

    capsys.readouterr()
    code = cli.main(["meter", "--vault", str(vault.root)])
    text, _ = capsys.readouterr()
    assert code == 0
    assert "pending: 1" in text and "retrieved_tokens: 1" in text


def test_summary_script_matches_package(vault, monkeypatch):
    monkeypatch.delenv("MEMEX_METER_PATH", raising=False)
    record(vault.root, route="mcp.read_note", text="abcdefgh", cited_slugs=["governed-memory"])
    path = vault.root / ".memex" / "meter.jsonl"
    expected = summarize(path)
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "meter_summary.py"),
         "--vault", str(vault.root), "--format", "json"],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == expected
    assert expected["pending"] == 1
    assert expected["hit"] == 0
