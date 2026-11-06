"""The summary script reads the meter JSONL and does not touch the network."""
import json
import subprocess
import sys

REPO = __import__("pathlib").Path(__file__).resolve().parents[2]


def test_summary_of_meter_format(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    path = vault / ".memex"
    path.mkdir()
    meter = path / "meter.jsonl"
    meter.write_text("\n".join([
        json.dumps({
            "v": 1, "ts": "2026-11-06T00:00:00+00:00", "route": "mcp.search_vault",
            "retrieved_tokens": 8, "cited_slugs": ["ada", "bush"], "hit": None,
            "query": "memory",
        }),
        json.dumps({
            "v": 1, "ts": "2026-11-06T00:00:01+00:00", "route": "memex.qa",
            "retrieved_tokens": 20, "cited_slugs": ["ada"], "hit": None,
        }),
        "{not json",
    ]) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "meter_summary.py"),
         "--path", str(meter), "--vault", str(vault), "--format", "json"],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    summary = json.loads(proc.stdout)
    assert summary["records"] == 2
    assert summary["skipped"] == 1
    assert summary["retrieved_tokens"] == 28
    assert summary["pending"] == 2
    assert summary["hit"] == 0 and summary["miss"] == 0
    assert summary["cited_slugs"] == {"ada": 2, "bush": 1}
    assert summary["by_route"]["mcp.search_vault"]["retrieved_tokens"] == 8
    event = json.loads(proc.stderr.strip().splitlines()[-1])
    assert event["cmd"] == "meter-summary" and event["ok"] is True


def test_missing_meter_file_is_empty_summary(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "meter_summary.py"),
         "--vault", str(vault), "--format", "json"],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    summary = json.loads(proc.stdout)
    assert summary["records"] == 0
    assert summary["retrieved_tokens"] == 0
    assert summary["pending"] == 0
