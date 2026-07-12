#!/usr/bin/env python3
"""Executable benchmark runner for the sample query set (roadmap Phase 3/6).

Measures the PRODUCT, not a copy of it: retrieval runs through `memex search
--format json` (the same deterministic BM25 the CLI and MCP server share).
Deterministic layer only — recall@k / MRR against each query's
expected_entities. The LLM rubric layers (citation, synthesis, …) remain
memex-evaluate's job; this runner is the reproducible floor under them, and the
gate RFC-005's hybrid retrieval must beat.

Usage:
  python3 scripts/run_benchmark.py --vault examples/fake-vault
  python3 scripts/run_benchmark.py --vault examples/fake-vault \\
      --memex-cmd "uv run --project memex-cli memex" --k 5 --json report.json

Exit 0 always for reporting; --min-recall FLOAT turns it into a CI gate.
"""
import argparse
import json
import pathlib
import shlex
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent


def load_queries(path: pathlib.Path) -> list[dict]:
    try:
        import yaml
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return data.get("queries", [])
    except ModuleNotFoundError:
        # stdlib fallback for the simple two-key schema of the sample set
        queries, cur = [], None
        for line in path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("- id:"):
                cur = {"id": s.split(":", 1)[1].strip().strip('"'),
                       "question": "", "expected_entities": []}
                queries.append(cur)
            elif cur is not None and s.startswith("question:"):
                cur["question"] = s.split(":", 1)[1].strip().strip('"')
            elif cur is not None and s.startswith("expected_entities:"):
                raw = s.split(":", 1)[1].strip().strip("[]")
                cur["expected_entities"] = [e.strip().strip('"') for e in raw.split(",") if e.strip()]
        return queries


def run_search(memex_cmd: str, vault: str, question: str, k: int) -> list[dict]:
    cmd = shlex.split(memex_cmd) + ["search", question, "--vault", vault,
                                    "--limit", str(k), "--format", "json"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"search failed: {' '.join(cmd)}\n{proc.stderr.strip()}")
    return json.loads(proc.stdout or "[]")


def score(hits: list[dict], expected: list[str], k: int) -> dict:
    got_paths = [h["path"].removesuffix(".md") for h in hits[:k]]
    got_slugs = [pathlib.Path(p).name for p in got_paths]
    found, ranks = [], []
    for e in expected:
        slug = pathlib.Path(e).name
        hit = e in got_paths or slug in got_slugs
        found.append(hit)
        if hit:
            idx = got_paths.index(e) if e in got_paths else got_slugs.index(slug)
            ranks.append(idx + 1)
    recall = sum(found) / len(expected) if expected else 1.0
    mrr = (1.0 / min(ranks)) if ranks else 0.0
    return {"recall": round(recall, 4), "mrr": round(mrr, 4),
            "missing": [e for e, f in zip(expected, found) if not f]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", default=str(REPO / "examples" / "fake-vault"))
    ap.add_argument("--queries", default=str(REPO / "evals" / "query-set.sample.yml"))
    ap.add_argument("--memex-cmd", default="memex",
                    help='how to invoke the CLI (e.g. "uv run --project memex-cli memex")')
    ap.add_argument("--k", type=int, default=5, help="retrieval depth (default 5)")
    ap.add_argument("--json", default=None, help="also write the report to this path")
    ap.add_argument("--min-recall", type=float, default=None,
                    help="exit 1 if mean recall@k falls below this (CI gate)")
    args = ap.parse_args()

    queries = load_queries(pathlib.Path(args.queries))
    if not queries:
        print("error: no queries found", file=sys.stderr)
        return 1

    rows = []
    for q in queries:
        try:
            hits = run_search(args.memex_cmd, args.vault, q["question"], args.k)
        except (RuntimeError, json.JSONDecodeError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        s = score(hits, q.get("expected_entities", []), args.k)
        rows.append({"id": q["id"], "question": q["question"], **s})

    mean_recall = round(sum(r["recall"] for r in rows) / len(rows), 4)
    mean_mrr = round(sum(r["mrr"] for r in rows) / len(rows), 4)
    report = {"cmd": "run_benchmark", "vault": args.vault, "k": args.k,
              "queries": len(rows), "mean_recall": mean_recall,
              "mean_mrr": mean_mrr, "rows": rows, "ok": True}

    for r in rows:
        flag = "" if not r["missing"] else f"  MISSING: {', '.join(r['missing'])}"
        print(f"{r['id']}  recall@{args.k}={r['recall']:.2f}  mrr={r['mrr']:.2f}{flag}")
    print(f"\nmean recall@{args.k}={mean_recall:.2f}  mean mrr={mean_mrr:.2f}  "
          f"({len(rows)} queries)")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}), file=sys.stderr)

    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.min_recall is not None and mean_recall < args.min_recall:
        print(f"FAIL: mean recall {mean_recall} < gate {args.min_recall}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
