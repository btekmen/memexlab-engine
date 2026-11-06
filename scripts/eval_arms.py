#!/usr/bin/env python3
"""Three-arm eval: model only, harness, harness + Memex retrieval.

Default model is a mock that does not use the network. LoCoMo questions come
from a local file (or ``--fetch``, which downloads the public dataset outside
the repo). Tekmen-eval questions must already live outside the repo.

Usage:
  python3 scripts/eval_arms.py locomo --data evals/locomo.sample.json --arms A
  python3 scripts/eval_arms.py locomo --data evals/locomo.sample.json --arms B
  python3 scripts/eval_arms.py locomo --data evals/locomo.sample.json --arms C
  python3 scripts/eval_arms.py locomo --fetch --model live --arms A,B,C

  python3 scripts/eval_arms.py tekmen --vault ~/vault --arms C
  TEKMEN_EVAL_PATH=~/vault/eval/tekmen-eval.yml python3 scripts/eval_arms.py tekmen --vault ~/vault
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import evalkit  # noqa: E402
from memex_cli.vault import Vault  # noqa: E402


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--arms", default="A,B,C",
                        help="comma-separated: A (model), B (harness), C (harness + retrieval)")
    parser.add_argument("--model", choices=["mock", "live"], default="mock",
                        help="mock is the default and makes no network call")
    parser.add_argument("--allow-remote", action="store_true",
                        help="with --model live, allow a hosted provider from the environment")
    parser.add_argument("--mock-answers", default=None,
                        help="JSON object of question text -> answer, used by --model mock")
    parser.add_argument("--k", type=int, default=6, help="notes retrieved on arm C (default 6)")
    parser.add_argument("--hit-at", type=float, default=0.5,
                        help="score at or above this sets meter hit=true (default 0.5)")
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--out", default=None, help="directory for report.md, report.json, results.jsonl")


def _build(args, env: dict):
    return evalkit.build_complete(
        args.model, allow_remote=args.allow_remote, mock_answers=args.mock_answers,
        env=env, max_tokens=args.max_tokens,
    )


def _emit(report: dict) -> None:
    summary = {k: v for k, v in report.items() if k != "rows"}
    print(json.dumps(summary, ensure_ascii=False), file=sys.stderr)
    for arm in report["arm_order"]:
        agg = report["arms"][arm]
        print(f"arm {arm} ({evalkit.ARM_LABEL[arm]}): accuracy={agg['accuracy']} "
              f"questions={agg['questions']} "
              f"median_retrieval_ms={agg['median_retrieval_ms']} "
              f"median_retrieved_tokens={agg['median_retrieved_tokens']}")
        for cat, slot in agg["by_category"].items():
            print(f"  {cat}: n={slot['n']} accuracy={slot['accuracy']}")
    print(f"wrote {report['out']}")


def main(argv: list[str] | None = None, env: dict | None = None) -> int:
    env = os.environ if env is None else env
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    loc = sub.add_parser("locomo", help="score a LoCoMo JSON file (public dataset, not vendored)")
    loc.add_argument("--data", default=None, help="path to locomo JSON (the synthetic sample or a download)")
    loc.add_argument("--fetch", action="store_true",
                     help="download the public locomo10.json into the cache (network)")
    loc.add_argument("--force-fetch", action="store_true", help="download again even if the cache exists")
    loc.add_argument("--limit", type=int, default=None, help="score at most this many questions")
    _add_common(loc)

    tek = sub.add_parser("tekmen", help="score a private question file that lives outside the repo")
    tek.add_argument("--vault", required=True, help="markdown vault to retrieve from on arm C")
    tek.add_argument("--questions", default=env.get("TEKMEN_EVAL_PATH"),
                     help="question file (or set TEKMEN_EVAL_PATH). Must be outside the repo")
    _add_common(tek)

    args = parser.parse_args(argv)
    try:
        arms = evalkit.parse_arms(args.arms)
        complete = _build(args, env)
        if args.command == "locomo":
            if args.fetch:
                data_path = evalkit.fetch_locomo(evalkit.default_locomo_cache(), force=args.force_fetch)
            elif args.data:
                data_path = evalkit.assert_locomo_data_allowed(Path(args.data))
            else:
                print("error: pass --data PATH or --fetch", file=sys.stderr)
                print("The public file is not in this repo. Obtain it with:", file=sys.stderr)
                print(f"  python3 scripts/eval_arms.py locomo --fetch", file=sys.stderr)
                print(f"  # saves {evalkit.default_locomo_cache()}", file=sys.stderr)
                print(f"  # or curl -L -o <outside>/locomo10.json {evalkit.LOCOMO_URL}", file=sys.stderr)
                return 1
            if not args.fetch:
                data_path = evalkit.assert_locomo_data_allowed(data_path)
            samples = evalkit.load_locomo(data_path)
            out = Path(args.out) if args.out else evalkit.ROOT / ".memex" / "eval" / "locomo"
            report = evalkit.run_locomo(
                samples, arms=arms, complete=complete, out=out, k=args.k,
                limit=args.limit, hit_at=args.hit_at, max_tokens=args.max_tokens,
            )
        else:
            if not args.questions:
                print("error: pass --questions or set TEKMEN_EVAL_PATH", file=sys.stderr)
                print("Format: evals/tekmen-eval.example.yml (synthetic; do not put real questions in the repo).",
                      file=sys.stderr)
                return 1
            qpath = evalkit.assert_tekmen_questions_allowed(Path(args.questions))
            vault = Vault(args.vault)
            questions = evalkit.load_tekmen(qpath)
            out = Path(args.out) if args.out else vault.root / ".memex" / "eval" / "tekmen"
            report = evalkit.run_tekmen(
                vault, questions, arms=arms, complete=complete, out=out, k=args.k,
                hit_at=args.hit_at, max_tokens=args.max_tokens,
            )
    except (ValueError, FileNotFoundError, PermissionError, RuntimeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(json.dumps({"cmd": "eval-arms", "ok": False, "error": str(exc)}), file=sys.stderr)
        return 1
    _emit(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
