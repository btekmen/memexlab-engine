"""Mock-model coverage for LoCoMo scoring, the three arms, and Tekmen-eval."""
import json
import os
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import evalkit  # noqa: E402
import guard_private_eval  # noqa: E402

SAMPLE = ROOT / "evals" / "locomo.sample.json"
EXAMPLE = ROOT / "evals" / "tekmen-eval.example.yml"


def test_porter_and_locomo_category_rules():
    assert evalkit.porter_stem("cats") == "cat"
    assert evalkit.porter_stem("running") == "run"
    assert evalkit.porter_stem("ties") == "tie"
    assert evalkit.porter_stem("skies") == "sky"
    assert evalkit.porter_stem("news") == "news"
    assert evalkit.porter_stem("dying") == "die"
    assert evalkit.porter_stem("enjoy") == "enjoy"
    assert evalkit.porter_stem("ace") == "ace"
    assert evalkit.porter_stem("useful") == "use"
    assert evalkit.f1_score("running cats", "run cat") == 1.0
    assert evalkit.score_locomo(4, "net-30", "net-30") == 1.0
    assert evalkit.score_locomo(3, "Portugal", "Portugal; on the Atlantic coast") == 1.0
    assert evalkit.score_locomo(2, "3 March 2026", "3 March 2026") == 1.0
    multi = evalkit.score_locomo(1, "July 2026, Lisbon", "July 2026, Lisbon")
    assert multi == 1.0
    partial = evalkit.score_locomo(1, "July 2026", "July 2026, Lisbon")
    assert partial == pytest.approx(0.5)
    assert evalkit.score_locomo(5, "no information available", "swordfish") == 1.0
    assert evalkit.score_locomo(5, "The password is swordfish", "swordfish") == 0.0
    assert evalkit.category_id("temporal") == 2


def test_tekmen_hit_accepts_answer_inside_a_sentence():
    score, hit = evalkit.score_tekmen("The review is 1 June 2026.", "1 June 2026", 0.5)
    assert hit is True and score > 0
    _, miss = evalkit.score_tekmen("no information available", "Lisbon", 0.5)
    assert miss is False


def test_locomo_three_arms_meter_and_prompts(tmp_path, monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("network")

    monkeypatch.setattr(evalkit.urllib.request, "urlopen", boom)
    seen = []

    def complete(system, user, max_tokens=256):
        seen.append((system, user))
        return "no information available"

    complete.route = "mock"
    out = tmp_path / "out"
    samples = evalkit.load_locomo(SAMPLE)
    report = evalkit.run_locomo(samples, arms=["A", "B", "C"], complete=complete, out=out, limit=1)
    assert [s for s, _ in seen][0].startswith("Answer the question")
    assert "Memex librarian" not in seen[0][0]
    assert "Memex librarian" in seen[1][0] and "(none)" in seen[1][0]
    assert "[[locomo-sample-northwind-s" in seen[2][0]
    assert report["arms"]["A"]["median_retrieval_ms"] is None
    assert report["arms"]["C"]["median_retrieval_ms"] is not None
    assert report["arms"]["C"]["median_retrieved_tokens"] > 0
    lines = (out / "meter.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["route"] == "eval.locomo" and rec["hit"] is False
    assert rec["v"] == 1 and isinstance(rec["retrieved_tokens"], int)
    assert isinstance(rec["cited_slugs"], list) and rec["cited_slugs"]
    assert (out / "report.md").is_file()
    assert (out / "results.jsonl").is_file()


def test_scripted_mock_scores_every_locomo_category(tmp_path):
    samples = evalkit.load_locomo(SAMPLE)
    answers = {qa["question"]: (
        "no information available" if qa["category"] == 5 else str(qa["answer"]).split(";")[0]
    ) for qa in samples[0]["qa"]}
    # multi-hop gold is already comma-separated; keep it whole
    answers[samples[0]["qa"][0]["question"]] = samples[0]["qa"][0]["answer"]
    blob = tmp_path / "answers.json"
    blob.write_text(json.dumps(answers), encoding="utf-8")
    complete = evalkit.build_complete("mock", mock_answers=str(blob), env={})
    out = tmp_path / "report"
    report = evalkit.run_locomo(samples, arms=["C"], complete=complete, out=out)
    agg = report["arms"]["C"]
    assert agg["questions"] == 5
    assert agg["accuracy"] == 1.0
    assert {row["category"] for row in json.loads(
        "[" + ",".join((out / "results.jsonl").read_text().splitlines()) + "]")} == {
        "multi-hop", "temporal", "open-domain", "single-hop", "adversarial"}
    hits = [json.loads(line)["hit"] for line in (out / "meter.jsonl").read_text().splitlines()]
    assert hits == [True, True, True, True, True]
    assert agg["median_retrieved_tokens"] > 0


def test_tekmen_file_outside_repo_and_rejects_in_repo(tmp_path, monkeypatch):
    monkeypatch.setattr(evalkit.urllib.request, "urlopen", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("network")))
    vault_root = tmp_path / "vault"
    (vault_root / "sessions").mkdir(parents=True)
    (vault_root / "sessions" / "sample-launch.md").write_text(
        "---\ntitle: Sample launch\n---\nThe synthetic launch review is 1 June 2026 in Lisbon.\n",
        encoding="utf-8",
    )
    questions = {
        "version": 1,
        "questions": [{
            "id": "q1",
            "category": "reminder",
            "question": "When is the synthetic launch review?",
            "answer": "1 June 2026",
            "expected_slugs": ["sample-launch"],
        }],
    }
    qpath = tmp_path / "tekmen-eval.local.yml"
    qpath.write_text(json.dumps(questions) if False else "version: 1\nquestions:\n  - id: q1\n    category: reminder\n    question: When is the synthetic launch review?\n    answer: '1 June 2026'\n    expected_slugs: [sample-launch]\n", encoding="utf-8")
    with pytest.raises(PermissionError):
        evalkit.assert_tekmen_questions_allowed(ROOT / "evals" / "query-set.sample.yml")
    loaded = evalkit.load_tekmen(evalkit.assert_tekmen_questions_allowed(EXAMPLE))
    assert [q["category"] for q in loaded] == ["reminder", "decision", "company-fact"]
    answers = tmp_path / "mock.json"
    answers.write_text(json.dumps({"When is the synthetic launch review?": "1 June 2026"}), encoding="utf-8")
    complete = evalkit.build_complete("mock", mock_answers=str(answers), env={})
    vault = evalkit.Vault(vault_root)
    out = tmp_path / "tekmen-out"
    report = evalkit.run_tekmen(vault, evalkit.load_tekmen(qpath), arms=["A", "C"], complete=complete, out=out)
    assert report["arms"]["C"]["accuracy"] == 1.0
    assert report["arms"]["C"]["by_category"]["reminder"]["n"] == 1
    rec = json.loads((vault_root / ".memex" / "meter.jsonl").read_text().splitlines()[-1])
    assert rec["route"] == "eval.tekmen" and rec["hit"] is True
    assert rec["cited_slugs"] == ["sample-launch"]
    row = json.loads((out / "results.jsonl").read_text().splitlines()[-1])
    assert row["arm"] == "C" and row["slugs_hit"] is True
    # arm A did not retrieve, so the meter has a single arm-C record
    assert len((vault_root / ".memex" / "meter.jsonl").read_text().splitlines()) == 1


def test_live_model_refuses_without_local_endpoint_and_does_not_call_out(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("network")

    monkeypatch.setattr(evalkit.urllib.request, "urlopen", boom)
    with pytest.raises(RuntimeError, match="MEMEX_MODEL_URL"):
        evalkit.build_complete("live", allow_remote=False, env={})


def test_cli_locomo_mock_and_missing_data(tmp_path):
    answers = tmp_path / "answers.json"
    samples = json.loads(SAMPLE.read_text(encoding="utf-8"))
    table = {}
    for qa in samples[0]["qa"]:
        table[qa["question"]] = "no information available" if qa["category"] == 5 else str(qa["answer"]).split(";")[0]
    table[samples[0]["qa"][0]["question"]] = samples[0]["qa"][0]["answer"]
    answers.write_text(json.dumps(table), encoding="utf-8")
    out = tmp_path / "cli-out"
    env = {k: v for k, v in os.environ.items() if k not in {"MEMEX_MODEL_URL", "MEMEX_METER_PATH"}}
    proc = __import__("subprocess").run(
        [sys.executable, str(ROOT / "scripts" / "eval_arms.py"), "locomo",
         "--data", str(SAMPLE), "--arms", "A,C", "--mock-answers", str(answers),
         "--out", str(out)],
        capture_output=True, text=True, env=env, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["arms"]["C"]["accuracy"] == 1.0
    assert report["arms"]["A"]["median_retrieved_tokens"] is None
    assert "arm C" in proc.stdout
    missing = __import__("subprocess").run(
        [sys.executable, str(ROOT / "scripts" / "eval_arms.py"), "locomo", "--arms", "A"],
        capture_output=True, text=True, env=env, check=False,
    )
    assert missing.returncode == 1
    assert "fetch" in missing.stderr
    inside = __import__("subprocess").run(
        [sys.executable, str(ROOT / "scripts" / "eval_arms.py"), "tekmen",
         "--vault", str(tmp_path), "--questions", str(ROOT / "evals" / "query-set.sample.yml"),
         "--out", str(tmp_path / "nope")],
        capture_output=True, text=True, env=env, check=False,
    )
    assert inside.returncode == 1
    assert "outside" in inside.stderr


def test_guard_allows_fixtures_and_flags_private_names(tmp_path):
    assert guard_private_eval.find_violations(ROOT) == []
    planted = tmp_path / "locomo10.json"
    planted.write_text("[]", encoding="utf-8")
    local = tmp_path / "tekmen-eval.local.yml"
    local.write_text("questions: []\n", encoding="utf-8")
    private = tmp_path / "evals" / "private"
    private.mkdir(parents=True)
    (private / "questions.yml").write_text("questions: []\n", encoding="utf-8")
    bad = guard_private_eval.find_violations(tmp_path)
    assert "locomo10.json" in bad
    assert "tekmen-eval.local.yml" in bad
    assert any(p.startswith("evals/private/") for p in bad)
    with pytest.raises(PermissionError):
        evalkit.assert_locomo_data_allowed(ROOT / "locomo10.json")
