# MemexLab runner — a self-hosted agent for your vault

A minimal, local-first agent loop that operates a markdown **vault** (its workspace)
using this repo's **Agent Skills** (its capabilities) and either a **local model** or a
**hosted API** (its reasoning) — switchable with one environment variable.

It runs on your own machine, reads and writes only inside the vault you point it at,
and pairs naturally with **Obsidian as the editor**: open the vault in Obsidian, run the
agent in a terminal against the same folder, and watch changes appear live.

> **Scope.** This is a *reference runner* — a dependency-light, runtime-agnostic proof
> that the skills + vault operate end to end, and a zero-infrastructure local option. It
> is not a daemon or a full agent platform. For the richer agent surface (background
> daemon, MCP, broader tooling), run [OpenClaw](https://github.com/openclaw/openclaw)
> against this repo's `skills/` — same skills, same vault.

## The four layers

| Layer | Here | Swap for |
| --- | --- | --- |
| **Workspace** | a markdown vault (`examples/fake-vault`) | your real vault (`--vault ~/vault`) |
| **Capabilities** | `skills/` (loaded as capability cards) | add/edit SKILL.md files |
| **Runtime** | `runner/agent.py` (this loop) | OpenClaw, for the full surface |
| **Model** | local or hosted (`MEMEX_PROVIDER`) | Ollama/vLLM ↔ Anthropic/OpenAI |

## Quickstart

```bash
# 0. See it load — no model, no keys, standard library only:
python3 runner/agent.py --dry-run --vault examples/fake-vault

# 1. Choose a backend (copy config.example.env, fill ONE block):
#    local model:
ollama serve & ollama pull llama3.1
export MEMEX_PROVIDER=local MEMEX_MODEL=llama3.1
pip install openai
#    …or a hosted API:
export MEMEX_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-...   # set your key
pip install anthropic

# 2. Give it a task against your workspace:
python3 runner/agent.py \
  --task "Summarize each note under people/ and list who they work with" \
  --vault examples/fake-vault
```

## How it works

1. **Loads skills** — parses `skills/*/SKILL.md` frontmatter into capability cards that
   go into the system prompt, so the model knows what it can do.
2. **Scopes the workspace** — every tool resolves paths against the vault root and
   refuses to escape it. The only mutating tool is `write_file`.
3. **Runs a ReAct loop** — the model emits one JSON action per turn
   (`list_files` · `read_file` · `write_file` · `search` · `validate` · `finish`); the
   runner executes it and feeds back the observation. This text protocol is identical
   across every backend, so switching local ↔ API needs no code changes.

## Provider switch

`MEMEX_PROVIDER` selects the backend (details in [`providers.py`](providers.py) and
[`config.example.env`](config.example.env)):

| `MEMEX_PROVIDER` | Backend | Needs |
| --- | --- | --- |
| `anthropic` | Anthropic Messages API | `pip install anthropic`, `ANTHROPIC_API_KEY` |
| `openai` | OpenAI Chat Completions | `pip install openai`, `OPENAI_API_KEY` |
| `local` | Ollama / vLLM / LM Studio (OpenAI-compatible) | `pip install openai`, a running server |

Local and hosted share one code path because Ollama, vLLM, and LM Studio all expose an
OpenAI-compatible `/v1` endpoint — so "self-hosted model" vs "hosted API" really is a
single env-var flip.

## Use with Obsidian

Point Obsidian at the same folder you pass to `--vault`. Edit and browse there; let the
agent ingest, link, and synthesize. Because the vault is just markdown on disk, both see
the same files with no sync layer in between.
