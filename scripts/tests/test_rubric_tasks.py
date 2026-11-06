"""Schema, deterministic rubric, three-arm wiring, and the private-file guard."""
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

EXAMPLE = ROOT / "evals" / "long-task.example.yml"
BRIEF = "Recommend payment terms for the fictional Sample Harbor Co-op launch."


def _task(**overrides):
    item = {
        "type": "long_task",
        "id": "sample-harbor-terms",
        "title": "Sample Harbor Co-op payment terms",
        "brief": BRIEF,
        "inputs": ["harbor-terms", "harbor-objection"],
        "assumptions": ["Sample Harbor Co-op is fictional."],
        "conflicts": [{"claim": "Sample Harbor already signed net-15.", "sources": ["harbor-objection"]}],
        "deliverable": "A one-page recommendation.",
        "max_score": 5,
        "rubric": [
            {"id": "terms", "description": "States net-45.", "weight": 3, "kind": "required", "check": "net-45"},
            {"id": "cites-terms", "description": "Cites the terms note.", "weight": 1, "kind": "required",
             "check": ["[[harbor-terms]]"]},
            {"id": "names-buyer", "description": "Names the buyer.", "weight": 1, "kind": "bonus",
             "check": "Sample Harbor"},
            {"id": "unsupported", "description": "Uncited objection.", "weight": 2, "kind": "penalty",
             "check": "unsupported_claims"},
        ],
    }
    item.update(overrides)
    return item


def test_example_file_validates_and_short_questions_still_load():
    loaded = evalkit.load_tekmen(evalkit.assert_tekmen_questions_allowed(EXAMPLE))
    assert loaded[0]["type"] == "long_task"
    assert loaded[0]["max_score"] == 5
    assert [c["kind"] for c in loaded[0]["rubric"]] == ["required", "required", "bonus", "penalty"]
    short = evalkit.load_tekmen(ROOT / "evals" / "tekmen-eval.example.yml")
    assert [q["type"] for q in short] == ["question", "question", "question"]


def test_schema_errors_name_the_field():
    with pytest.raises(ValueError, match="rubric terms kind"):
        evalkit.validate_long_task(_task(rubric=[{
            "id": "terms", "description": "x", "weight": 1, "kind": "maybe",
        }]))
    with pytest.raises(ValueError, match="conflicts\\[0\\].sources"):
        bad = _task()
        bad["conflicts"] = [{"claim": "A claim.", "sources": []}]
        evalkit.validate_long_task(bad)
    with pytest.raises(ValueError, match="max_score"):
        evalkit.validate_long_task(_task(max_score=0))
    with pytest.raises(ValueError, match="inputs must not be empty"):
        evalkit.validate_long_task(_task(inputs=[]))
    with pytest.raises(ValueError, match="duplicated"):
        evalkit.validate_long_task(_task(rubric=[
            {"id": "terms", "description": "x", "weight": 1, "kind": "required", "check": "a"},
            {"id": "terms", "description": "y", "weight": 1, "kind": "bonus", "check": "b"},
        ]))


def test_deterministic_grader_hits_citations_and_penalties():
    task = evalkit.validate_long_task(_task())
    memo = (
        "Recommend net-45 for Sample Harbor. See [[harbor-terms]]. "
        "Sample Harbor already signed net-15."
    )
    graded = evalkit.grade_long_task(task, memo)
    by = {row["id"]: row for row in graded["criteria"]}
    assert by["terms"]["earned"] == 3
    assert by["cites-terms"]["earned"] == 1
    assert by["names-buyer"]["earned"] == 1
    assert by["unsupported"]["earned"] == -2
    assert graded["unsupported_claims"] == ["Sample Harbor already signed net-15."]
    assert graded["weighted_total"] == 3
    assert graded["score"] == 0.6
    assert graded["prediction_slugs"] == ["harbor-terms"]
    clean = "Recommend net-45 for Sample Harbor. See [[harbor-terms]]."
    clean_grade = evalkit.grade_long_task(task, clean)
    assert clean_grade["weighted_total"] == 5
    assert clean_grade["score"] == 1
    cited = evalkit.grade_long_task(
        task, "Recommend net-45. Sample Harbor already signed net-15. [[harbor-objection]]"
    )
    assert cited["unsupported_claims"] == []
    assert next(row for row in cited["criteria"] if row["id"] == "unsupported")["earned"] == 0


def test_three_arms_use_mock_model_and_a_larger_budget(tmp_path, monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("network")

    monkeypatch.setattr(evalkit.urllib.request, "urlopen", boom)
    vault_root = tmp_path / "vault"
    (vault_root / "notes").mkdir(parents=True)
    (vault_root / "notes" / "harbor-terms.md").write_text(
        "---\ntitle: Sample Harbor terms\n---\nSample Harbor Co-op terms are net-45.\n",
        encoding="utf-8",
    )
    (vault_root / "notes" / "harbor-objection.md").write_text(
        "---\ntitle: Sample Harbor objection\n---\nA draft claimed Sample Harbor already signed net-15.\n",
        encoding="utf-8",
    )
    (vault_root / "notes" / "unrelated.md").write_text(
        "---\ntitle: Unrelated\n---\nThis note is about orchards.\n",
        encoding="utf-8",
    )
    qpath = tmp_path / "long-task.local.yml"
    qpath.write_text(yaml_task(), encoding="utf-8")
    seen = []

    def complete(system, user, max_tokens=256):
        seen.append((system, user, max_tokens))
        return (
            "Recommend net-45 for Sample Harbor. See [[harbor-terms]]. "
            "The objection is cited in [[harbor-objection]]."
        )

    complete.route = "mock"
    out = tmp_path / "out"
    report = evalkit.run_tekmen(
        evalkit.Vault(vault_root), evalkit.load_tekmen(qpath),
        arms=["A", "B", "C"], complete=complete, out=out, k=2,
        long_k=2, long_max_tokens=2048, judge=None,
    )
    assert [call[2] for call in seen] == [2048, 2048, 2048]
    assert "Memex librarian" not in seen[0][0]
    assert "Retrieved notes:\n(none)" in seen[1][0]
    assert "[[harbor-terms]]" in seen[2][0] and "net-45" in seen[2][0]
    assert "[[harbor-objection]]" in seen[2][0]
    assert "orchards" not in seen[2][0]
    arm_c = report["arms"]["C"]
    assert arm_c["long_tasks"][0]["weighted_total"] == 5
    assert arm_c["long_tasks"][0]["criteria"][0]["id"] == "terms"
    assert arm_c["accuracy"] == 1.0
    assert arm_c["median_retrieved_tokens"] > 0
    assert report["arms"]["A"]["median_retrieval_ms"] is None
    lines = (vault_root / ".memex" / "meter.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["route"] == "eval.long_task" and rec["hit"] is True
    assert "weighted 5" in (out / "report.md").read_text(encoding="utf-8")
    row = json.loads((out / "results.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert row["arm"] == "C" and row["type"] == "long_task" and row["weighted_total"] == 5


def test_live_judge_refuses_without_a_local_endpoint(tmp_path, monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("network")

    monkeypatch.setattr(evalkit.urllib.request, "urlopen", boom)
    env = {k: v for k, v in os.environ.items() if k not in {"MEMEX_MODEL_URL", "MEMEX_METER_PATH"}}
    proc = __import__("subprocess").run(
        [sys.executable, str(ROOT / "scripts" / "eval_arms.py"), "tekmen",
         "--vault", str(tmp_path), "--questions", str(EXAMPLE),
         "--judge", "live", "--arms", "A", "--out", str(tmp_path / "out")],
        capture_output=True, text=True, env=env, check=False,
    )
    assert proc.returncode == 1
    assert "MEMEX_MODEL_URL" in proc.stderr


def test_guard_allows_the_example_and_flags_other_long_task_names(tmp_path):
    assert guard_private_eval.find_violations(ROOT) == []
    (tmp_path / "long-task.local.yml").write_text("questions: []\n", encoding="utf-8")
    (tmp_path / "deals").mkdir()
    (tmp_path / "deals" / "acme-long_task.yml").write_text("questions: []\n", encoding="utf-8")
    bad = guard_private_eval.find_violations(tmp_path)
    assert "long-task.local.yml" in bad
    assert "deals/acme-long_task.yml" in bad


def yaml_task() -> str:
    return (
        "version: 1\nquestions:\n"
        "  - type: long_task\n"
        "    id: sample-harbor-terms\n"
        "    title: Sample Harbor Co-op payment terms\n"
        f"    brief: {BRIEF!r}\n"
        "    inputs: [harbor-terms, harbor-objection]\n"
        "    assumptions: ['Sample Harbor Co-op is fictional.']\n"
        "    conflicts:\n"
        "      - claim: Sample Harbor already signed net-15.\n"
        "        sources: [harbor-objection]\n"
        "    deliverable: A one-page recommendation.\n"
        "    max_score: 5\n"
        "    rubric:\n"
        "      - {id: terms, description: States net-45., weight: 3, kind: required, check: net-45}\n"
        "      - {id: cites-terms, description: Cites the terms note., weight: 1, kind: required, check: ['[[harbor-terms]]']}\n"
        "      - {id: names-buyer, description: Names the buyer., weight: 1, kind: bonus, check: Sample Harbor}\n"
        "      - {id: unsupported, description: Uncited objection., weight: 2, kind: penalty, check: unsupported_claims}\n"
    )
