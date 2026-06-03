#!/usr/bin/env python3
"""MemexLab reference runner — a minimal, self-hosted agent that operates a vault.

This is a small, dependency-light agent loop you can run locally on your own machine.
It loads the repo's Agent Skills as capabilities, treats a markdown vault as its
workspace, and reasons with either a local model or a hosted API (switchable via the
MEMEX_PROVIDER env var — see providers.py).

It is intentionally minimal: a runtime-agnostic proof that the skills + vault operate
end to end, and a zero-infrastructure local option. For the full agent surface (daemon,
richer tooling, MCP), use OpenClaw — https://github.com/openclaw/openclaw — pointed at
this repo's skills/. The skills and vault are the same either way.

Usage:
    python3 runner/agent.py --task "List the people notes and summarize each" \\
        --vault examples/fake-vault

    python3 runner/agent.py --dry-run --vault examples/fake-vault   # no model call
"""
import argparse
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import providers  # noqa: E402
from tools import Workspace  # noqa: E402

SKILLS_DIR = ROOT / "skills"
VALIDATE_SCRIPT = str(ROOT / "scripts" / "validate_vault.py")

FRONTMATTER = re.compile(r"^---\n(.*?)\n---", re.S)
ACTION_BLOCK = re.compile(r"```action\s*(.*?)```", re.S)


def load_skills():
    """Read skills/*/SKILL.md frontmatter into (name, description) capability cards."""
    cards = []
    if not SKILLS_DIR.is_dir():
        return cards
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        m = FRONTMATTER.search(text)
        name = skill_md.parent.name
        desc = ""
        if m:
            for line in m.group(1).splitlines():
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip()
                elif line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip()
        cards.append((name, desc))
    return cards


def build_system_prompt(ws, skills):
    skill_lines = "\n".join("- {}: {}".format(n, d) for n, d in skills)
    files = ws.list_files()
    sample = "\n".join("  " + f for f in files[:25])
    more = "" if len(files) <= 25 else "\n  … and {} more".format(len(files) - 25)
    return """You are the MemexLab agent. Your workspace is a local markdown knowledge vault at:
    {root}
It currently holds {n} markdown files:
{sample}{more}

Your capabilities (Agent Skills available in this repo):
{skills}

You operate the vault ONLY through these tools, one per turn:
- list_files(glob)         list vault files (glob defaults to **/*.md)
- read_file(path)          read one file (path relative to the vault)
- write_file(path, content) create/overwrite a file inside the vault
- search(query)            full-text search across the vault
- validate()               run the vault validator (frontmatter/type/marker rules)
- finish(answer)           end the task and return your answer

PROTOCOL: respond with your brief reasoning, then EXACTLY ONE action as a JSON object
inside a fenced block, like:

```action
{{"tool": "search", "args": {{"query": "Grace Hopper"}}}}
```

Rules: every new file must start with `---` frontmatter containing a `type:` field.
Cite the files you used. Stop with finish() as soon as the task is done.""".format(
        root=ws.root, n=len(files), sample=sample or "  (empty)", more=more,
        skills=skill_lines or "- (none found)",
    )


def parse_action(text):
    m = ACTION_BLOCK.search(text)
    blob = m.group(1).strip() if m else None
    if blob is None:
        # tolerate a bare JSON object
        m2 = re.search(r"\{.*\}", text, re.S)
        blob = m2.group(0) if m2 else None
    if not blob:
        return None, None, "no action block found"
    try:
        obj = json.loads(blob)
    except json.JSONDecodeError as e:
        return None, None, "invalid JSON action: {}".format(e)
    return obj.get("tool"), obj.get("args", {}) or {}, None


def run_tool(ws, tool, args):
    if tool == "list_files":
        return "\n".join(ws.list_files(args.get("glob", "**/*.md"))) or "(no files)"
    if tool == "read_file":
        return ws.read_file(args["path"])
    if tool == "write_file":
        return ws.write_file(args["path"], args["content"])
    if tool == "search":
        return "\n".join(ws.search(args["query"])) or "(no matches)"
    if tool == "validate":
        return ws.validate(VALIDATE_SCRIPT)
    return "unknown tool: {}".format(tool)


def dry_run(ws, skills):
    cfg = providers.resolved()
    print("MemexLab runner — dry run (no model call)\n")
    print("Backend:")
    print("  provider : {}".format(cfg["provider"]))
    print("  model    : {}".format(cfg["model"]))
    print("  endpoint : {}".format(cfg["endpoint"]))
    print("\nWorkspace:")
    st = ws.stats()
    print("  root           : {}".format(st["root"]))
    print("  markdown files : {}".format(st["markdown_files"]))
    print("\nCapabilities ({} skills loaded):".format(len(skills)))
    for n, d in skills:
        print("  - {}: {}".format(n, d))
    print("\nTools: list_files, read_file, write_file, search, validate, finish")
    print("\nReady. Set MEMEX_PROVIDER + key/endpoint and drop --dry-run to run a task.")


def main():
    ap = argparse.ArgumentParser(description="MemexLab self-hosted reference agent")
    ap.add_argument("--task", help="the instruction for the agent")
    ap.add_argument("--vault", default="examples/fake-vault", help="workspace path")
    ap.add_argument("--max-steps", type=int, default=12)
    ap.add_argument("--dry-run", action="store_true",
                    help="load skills + workspace and print config; no model call")
    args = ap.parse_args()

    ws = Workspace(args.vault if os.path.isabs(args.vault) else ROOT / args.vault)
    skills = load_skills()

    if args.dry_run:
        dry_run(ws, skills)
        return
    if not args.task:
        sys.exit("--task is required (or use --dry-run)")

    system = build_system_prompt(ws, skills)
    messages = [{"role": "user", "content": args.task}]
    print(">> task: {}\n".format(args.task))

    for step in range(1, args.max_steps + 1):
        reply = providers.complete(system, messages)
        tool, targs, err = parse_action(reply)
        if err:
            print("[step {}] {}".format(step, err))
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user",
                             "content": "Reply with one valid ```action``` block."})
            continue
        print("[step {}] {} {}".format(step, tool, json.dumps(targs)[:120]))
        if tool == "finish":
            print("\n=== ANSWER ===\n{}".format(targs.get("answer", "")))
            return
        try:
            obs = run_tool(ws, tool, targs)
        except Exception as e:  # tool errors are fed back, not fatal
            obs = "tool error: {}".format(e)
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user",
                         "content": "Observation:\n{}".format(obs)[:6000]})
    print("\n(reached max steps without finish())")


if __name__ == "__main__":
    main()
