# Automation and Scripts

Automation in MemexLab is restrained on purpose. There is no background daemon, no watcher, no auto-sync. Every automated action is invoked explicitly — by you, by cron, or by an editor hotkey. The machinery is deterministic everywhere except where a language model is explicitly called; those call sites are named and logged.

## What counts as automation

Three layers:

- The engine CLI (`memex`). Eight modes, each a separate command. This is the primary automation surface.

- Scheduled scripts (`scripts/`). Cron-friendly wrappers around engine calls. Currently one: `scripts/lint_daily.py`.

- Obsidian plugins. Templater (templates), Dataview (in-vault queries), optionally a capture plugin. These run inside the editor, not the CLI.

Nothing else. If a new automation is proposed, it has to fit one of these layers, not introduce a fourth.

## The engine, command-by-command

Invoked from the shell (or `uv run python -m memex`). Full surface:

```
memex doctor   [--vault PATH] [--api] [--json]memex migrate  [--vault PATH] [--apply] [--json]memex rollback [SNAPSHOT_ID] [--vault PATH] [--apply] [--list] [--json]memex compile  <source_path> [--title T] [--problem N] [--apply] [--vault PATH] [--json]memex lint     [--folder wiki] [--output-dated] [--apply] [--vault PATH] [--json]memex qa       "<question>" [--file PATH] [--apply] [--vault PATH] [--json]memex index    "<topic>" --type {topic,reading-order,concept-map,category,problem-view}                         [--file PATH] [--apply] [--limit N] [--vault PATH] [--json]memex export essay   "<topic>" [--file PATH] [--apply] [--limit N] [--vault PATH] [--json]memex export slides  "<topic>" [--file PATH] [--apply] [--limit N] [--theme NAME] [--vault PATH] [--json]memex chart    <kind> [--top N] [--since YYYY-MM-DD] [--bucket day|week|month] [--apply] [--vault PATH] [--json]
```

Every command shares a set of conventions.

### Conventions

Dry-run by default. Every mutating command prints a plan and exits without touching the vault unless you pass `--apply`. This is not a gentle default; it is the contract. A fresh invocation cannot accidentally delete your work.

Atomic writes. Every file written by the engine is written via `tempfile + os.replace`. Half-written files do not exist — either the old content is still there, or the new content is.

Snapshots before apply. `migrate` and `compile` copy every file they will change to `.memex/snapshots/<id>/` with a `manifest.json` describing the intended changes. `memex rollback` replays a snapshot in reverse.

Idempotent where possible. `migrate` is idempotent: a second `--apply` run on an already-migrated vault produces zero changes. `lint` is idempotent (same vault, same report). `compile` is not idempotent — re-running it on the same source produces new candidate notes (LLMs are non-deterministic), which is why compile carries its own review step.

Structured logging. One JSON event per invocation to stderr; operators pipe this to `.memex/log.jsonl`.

Exit codes. `0` on success, `1` on any error. `lint` returns `1` if any error-severity findings fire. Config and vault errors also return `1`.

`--json` output. Every mutating command has a `--json` flag that emits the plan or report as machine-readable JSON on stdout. Use in scripts; use the default text output in terminals.

### Per-command notes

`doctor`. Fast config sanity check. No writes, ever. Verifies your LLM provider API key (e.g. `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`), confirms the vault path exists and has the expected folder shape, optionally pings the provider API (`--api`).

`migrate`. Brings an existing vault’s frontmatter up to current schemas. Three rules: `inject_core` (writes missing core-note frontmatter), `rewrite_core_type` (fixes a curated-type core note), `backfill_latticework` (adds empty `latticework: []` to curated notes missing the field). Always dry-run by default; always snapshots before apply.

`rollback`. The inverse of `migrate --apply`. Takes a snapshot ID (or uses the latest) and restores files exactly as they were.

`compile`. LLM-driven. Reads a raw source, sends it plus the two core notes to the model, receives a list of candidate atomic notes. Writes them into `wiki/` on `--apply`. Slug collisions are auto-suffixed.

`lint`. Deterministic. Five checks: frontmatter validity (error), broken wiki-links (error), orphan atomic articles (warn), stub bodies (info), missing `latticework` on curated (info). Error findings fail the run.

`qa`. LLM-driven. BM25 retrieval over the wiki, LLM produces an answer with `[[slug]]` citations, validated against the vault. Empty context or unknown citations become warnings, not errors.

`index`. LLM-driven. Wider retrieval than `qa`; per-type prompts for five flavours (`topic`, `reading-order`, `concept-map`, `category`, `problem-view`). Writes a structured note under `_index/`.

`export essay` / `export slides`. LLM-driven. Same retrieval layer as `index`, different output shapes. Essays are full atomic notes under `_essays/`; slides are Marp-compatible decks under `_slides/`.

`chart`. No LLM. Aggregates vault metadata into one of four chart kinds (`tag-frequency`, `type-distribution`, `latticework-coverage`, `timeline`) and writes a PNG plus sidecar note under `_charts/`.

## Scheduled scripts

### scripts/lint_daily.py

A cron-friendly wrapper around `memex lint --apply --output-dated`. It writes a dated report to `_lint/lint-YYYY-MM-DD.md`, emits one structured JSON event to stderr (`lint_daily_complete` | `lint_daily_config_error` | `lint_daily_vault_error` | `lint_daily_lint_error`), and propagates the lint report’s exit code.

```
0 6 * * * cd ~/memex && uv run python scripts/lint_daily.py \    2>> ~/Documents/Obsidian/<your-vault>/.memex/log.jsonl
```

This single line gives you a daily health check without hand-invocation. If you subscribe to the log file (for example, tailing it into Apple Mail or a Slack webhook on your own system), lint regressions surface immediately.

### Future scripts

Three obvious candidates, none yet implemented:

- `scripts/inbox_triage.py` — nightly report on inbox age, flagging items older than seven days.

- `scripts/weekly_digest.py` — a summary of what changed in the vault this week (new notes, promoted notes, new raw sources).

- `scripts/archive_old_daily_notes.py` — moves daily notes older than N days to `archive/daily/`.

Each would follow the `lint_daily.py` shape: argparse, load settings, call the engine, emit one JSON event, return a sensible exit code. New scripts belong in `scripts/` and get their own docs section here.

## How LLMs interact with the system

The engine’s LLM integration is concentrated in a single module (`memex.llm`) and a single client (`LLMClient`). Every LLM-driven command — `compile`, `qa`, `index`, `export essay`, `export slides` — routes through this client.

### The contract

- Structured outputs. Every LLM call expects a Pydantic schema. The response is parsed and validated. On parse/validation failure the call is retried once with the validation error fed back, then surfaces as `LLMOutputError`.

- Retries on transient errors. `RateLimitError`, `APIConnectionError`, `APITimeoutError`, `InternalServerError` are retried up to three times with exponential backoff + jitter.

- Terminal failures. Auth errors, bad requests — raise immediately as `LLMError`. No retry.

- One event per call. Model, max tokens, attempts, latency, prompt/response sizes — one JSON line.

### Prompt files

All system prompts live under `prompts/` as plain markdown:

```
prompts/  compile.md  qa.md  index/    topic.md    reading-order.md    concept-map.md    category.md    problem-view.md  export/    essay.md    slides.md
```

Editing a prompt changes the engine’s behaviour on the next run. No code redeploy required. Prompts are the “skill files” referenced elsewhere in these docs — they are where model-level instructions live.

### Context construction

Every LLM-driven mode uses the same context-building logic, in `memex.retrieval.bm25`:

- The two core notes are always included.

- BM25 ranks the remaining notes against the query (compile’s query is the raw source text; qa/index/essay/slides use the user’s topic).

- The top-ranked notes are taken until a token budget fills (~25k for `qa`, ~35k for `index`/`essay`/`slides`).

- Notes that would overflow the budget are skipped, not truncated.

Retrieval is deterministic. The same vault + same query returns the same context, always. This matters because it decouples debugging: if the output is wrong, you can check whether retrieval brought the right notes or the model used them wrong.

### Safe operating rules

Rule 1 — Dry-run first, always. An `--apply` invocation you haven’t first seen as a dry-run is a bug. This is not about trust; it is about habit.

Rule 2 — Review LLM outputs before letting them influence future work. An unreviewed compile output that you’ve `--apply`-ed but haven’t read is going to distort every future retrieval. If you don’t have time to review now, `--apply` later.

Rule 3 — Never let the LLM write directly into the wiki without citation trace. Every engine-written note carries a `source:` field (for compile output) or a `cited_slugs` reference chain (for qa/essay/etc.). A note without provenance shouldn’t be in the wiki.

Rule 4 — Treat the API key as PII-level sensitive. Keep your provider API key (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, …) in your shell environment only, not in `.env`, not in any file under version control. If you accidentally commit one, rotate immediately.

Rule 5 — Keep prompt edits auditable. Prompts are version-controlled alongside the engine. A behaviour regression traces back to a prompt diff, not a mystery.

Rule 6 — No multi-step agent loops. The engine never chains LLM calls. Each mode is one prompt, one response, parsed and committed. If you find yourself wanting a multi-step agent, that is a signal for a new, named mode — not a generic loop.

## Logging

Every engine invocation emits JSON events to stderr. Operators redirect stderr to `.memex/log.jsonl`:

```
memex compile raw/... 2>> ~/Documents/Obsidian/<your-vault>/.memex/log.jsonl
```

A sample event:

```
{"event":"compile_complete","model":"<your-model>","attempts":1,"latency_ms":4320, "source":"raw/2026-03-17-bloomberg-stablecoin-settlement-rails.md","candidates":4, "applied":true,"level":"info","timestamp":"2026-03-18T09:04:12Z"}
```

The log is append-only and human-readable. Grepping it is the standard way to answer “did anything go wrong this week?”.

## What automation will never do

- Auto-promote. `status: seed` → `draft` → `evergreen` is strictly manual.

- Auto-merge. Duplicate-detection is a linter finding, not a fix.

- Auto-generate without review. No “write every morning’s essay” cron. The engine generates on demand only.

- Delete anything without explicit confirmation. The engine’s only deletions happen on `rollback`, and they are restorations to a prior state, never destructive in the forward direction.

These are policy, not limitation. The system is deliberately less than it could be, because the value of a second brain is trust, and trust is eroded by surprises.

---

[← Metadata and Tagging Rules](07-metadata-and-tagging-rules.md) · [Docs index](README.md) · [User Modes →](09-user-modes.md)
