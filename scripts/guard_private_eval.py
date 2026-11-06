#!/usr/bin/env python3
"""Fail if a private Tekmen-eval set or the LoCoMo download is inside the repo.

The synthetic fixtures are allowed:
  evals/tekmen-eval.example.yml
  evals/long-task.example.yml
  evals/locomo.sample.json

Anything named locomo10.json, tekmen-eval.local.*, long-task.local.*, or any
other file whose name contains long-task / long_task, or sitting under
evals/private/, is a violation. Real Tekmen-eval questions and real long tasks
stay outside the repository.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".git", ".venv", "venv", "site", "__pycache__", ".memex", "node_modules"}
ALLOW = {
    Path("evals/tekmen-eval.example.yml"),
    Path("evals/long-task.example.yml"),
    Path("evals/locomo.sample.json"),
}


def find_violations(root: Path) -> list[str]:
    root = Path(root)
    found = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if SKIP.intersection(rel.parts):
            continue
        if rel in ALLOW:
            continue
        name = path.name
        lowered = name.casefold()
        if (name == "locomo10.json" or name.startswith("tekmen-eval.local.")
                or name.startswith("long-task.local.")
                or "long-task" in lowered or "long_task" in lowered):
            found.append(str(rel))
            continue
        if "evals" in rel.parts and "private" in rel.parts:
            found.append(str(rel))
    return sorted(set(found))


def main() -> int:
    bad = find_violations(ROOT)
    if bad:
        print("private eval files must not live in this repo:", file=sys.stderr)
        for rel in bad:
            print(f"  {rel}", file=sys.stderr)
        return 1
    print("OK: no private Tekmen-eval set and no vendored locomo10.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
