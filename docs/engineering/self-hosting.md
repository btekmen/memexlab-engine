# Self-hosting the agent

MemexLab ships a small, **runnable** reference agent so you can operate a vault on your own
machine today — local-first, with a backend you choose. It is the executable counterpart to
the skills and schemas the rest of these docs describe.

> Browse the code: [`runner/`](https://github.com/btekmen/memexlab-engine/tree/main/runner).
> Try it with no API key and no model:
> `python3 runner/agent.py --dry-run --vault examples/fake-vault`.

## The four layers

A self-hosted agent is four layers, and MemexLab gives you each one:

| Layer | What it is | In this repo |
| --- | --- | --- |
| **Workspace** | the agent's working directory | a markdown **vault** (e.g. `examples/fake-vault`, or your own) |
| **Capabilities** | what the agent knows how to do | [`skills/`](https://github.com/btekmen/memexlab-engine/tree/main/skills) — loaded into the system prompt |
| **Runtime** | the loop that reasons + calls tools | [`runner/agent.py`](https://github.com/btekmen/memexlab-engine/blob/main/runner/agent.py) (here) or **OpenClaw** (full surface) |
| **Model** | the reasoning backend | local *or* hosted — one env var (`MEMEX_PROVIDER`) |

## Switchable backend — local or hosted

The reasoning backend flips on a single environment variable. Local and hosted share one code
path because Ollama, vLLM, and LM Studio all expose an OpenAI-compatible `/v1` endpoint — so
"self-hosted model" vs "hosted API" is genuinely one flip, not a rewrite.

| `MEMEX_PROVIDER` | Backend | Needs |
| --- | --- | --- |
| `anthropic` | Anthropic Messages API | `pip install anthropic`, `ANTHROPIC_API_KEY` |
| `openai` | OpenAI Chat Completions | `pip install openai`, `OPENAI_API_KEY` |
| `local` | Ollama / vLLM / LM Studio (air-gapped) | `pip install openai`, a running local server |

## Run it

```bash
# 0. See it load — standard library only, no key, no model:
python3 runner/agent.py --dry-run --vault examples/fake-vault

# 1a. Fully local (nothing leaves the machine):
ollama serve & ollama pull llama3.1
export MEMEX_PROVIDER=local MEMEX_MODEL=llama3.1 && pip install openai

# 1b. …or a hosted API:
export MEMEX_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-...   # your key
pip install anthropic

# 2. Give it a task against your workspace:
python3 runner/agent.py --task "Summarize each note under people/" --vault examples/fake-vault
```

## How the loop works

1. **Loads skills** — parses each `skills/*/SKILL.md` into a capability card in the system prompt.
2. **Scopes the workspace** — every tool resolves paths against the vault root and refuses to
   escape it; the only mutating tool is `write_file`.
3. **Runs a ReAct loop** — the model emits one JSON action per turn
   (`list_files` · `read_file` · `write_file` · `search` · `validate` · `finish`); the runner
   executes it and feeds the observation back. This text protocol is identical across every
   backend, so switching local ↔ hosted needs no code change.

## Pair with Obsidian

Point Obsidian at the same folder you pass to `--vault`. Edit and browse there; let the agent
ingest, link, and synthesize. The vault is just markdown on disk, so both see the same files
with no sync layer between them.

## Reference runner vs. OpenClaw

The runner here is intentionally minimal — a runtime-agnostic proof that the skills + vault
operate end to end, and a zero-infrastructure local option. For the fuller agent surface
(background daemon, MCP, broader tooling), run [OpenClaw](https://github.com/openclaw/openclaw)
against this repo's `skills/`. Same skills, same vault, either way.

---

[← Library](library.md) · [Engineering & design](README.md)
