import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from run_benchmark import load_queries, score  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent.parent


def test_score_full_recall_and_rank():
    hits = [{"path": "companies/acme-bank.md"}, {"path": "people/ada-stone.md"}]
    s = score(hits, ["companies/acme-bank", "people/ada-stone"], k=5)
    assert s["recall"] == 1.0 and s["mrr"] == 1.0 and s["missing"] == []


def test_score_partial_and_missing():
    hits = [{"path": "concepts/other.md"}, {"path": "people/ada-stone.md"}]
    s = score(hits, ["companies/acme-bank", "people/ada-stone"], k=5)
    assert s["recall"] == 0.5
    assert s["mrr"] == 0.5  # best expected hit at rank 2
    assert s["missing"] == ["companies/acme-bank"]


def test_score_respects_k():
    hits = [{"path": f"n{i}.md"} for i in range(4)] + [{"path": "people/ada-stone.md"}]
    s = score(hits, ["people/ada-stone"], k=3)
    assert s["recall"] == 0.0


def test_load_queries_sample_set():
    queries = load_queries(REPO / "evals" / "query-set.sample.yml")
    assert [q["id"] for q in queries] == ["q001", "q002"]
    assert queries[0]["expected_entities"] == ["companies/acme-bank", "people/ada-stone"]


def test_end_to_end_with_stub_cli(tmp_path):
    stub = tmp_path / "stub.py"
    stub.write_text(
        "import json,sys\n"
        "print(json.dumps([{'slug':'acme-bank','path':'companies/acme-bank.md'},"
        "{'slug':'ada-stone','path':'people/ada-stone.md'},"
        "{'slug':'platform-banking','path':'concepts/platform-banking.md'},"
        "{'slug':'platform-banking-note','path':'sources/platform-banking-note.md'}]))\n",
        encoding="utf-8")
    out = tmp_path / "report.json"
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "run_benchmark.py"),
         "--vault", str(REPO / "examples" / "fake-vault"),
         "--memex-cmd", f"{sys.executable} {stub}",
         "--json", str(out), "--min-recall", "0.9"],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    report = json.loads(out.read_text())
    assert report["mean_recall"] == 1.0 and report["queries"] == 2


def test_min_recall_gate_fails(tmp_path):
    stub = tmp_path / "stub.py"
    stub.write_text("print('[]')\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "run_benchmark.py"),
         "--memex-cmd", f"{sys.executable} {stub}", "--min-recall", "0.5"],
        capture_output=True, text=True)
    assert proc.returncode == 1 and "FAIL" in proc.stderr
