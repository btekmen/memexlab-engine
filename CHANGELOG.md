# Changelog

All notable changes to the MemexLab Engine framework.

## Unreleased

### Added

- Cross-tool local memory contract on `memexlab-mcp`: `get_index` (compact
  prompt index, no bodies), plus idempotent `capture_note(origin_ref=)`. The
  same `origin_ref` returns the existing note and does not write or edit.
  Writes stay inside the governed write dir (default `inbox/`). Existing tools
  are unchanged when `origin_ref` is omitted.
- Local retrieval meter. `get_index`, `search_vault`, `read_note`, `memex search`,
  and `memex qa` append one JSONL record (`v`, `ts`, `route`, `retrieved_tokens`,
  `cited_slugs`, `hit: null`) to `<vault>/.memex/meter.jsonl`. No network.
  `MEMEX_METER_PATH` or `meter_path:` in `governance.yml` moves the file.
  Summarize with `memex meter` or `python3 scripts/meter_summary.py`.
- `docs/plans/living-brain-adoption.md` — order and PR split for the five
  local-only Living Brain ideas. Items 1 and 5, then item 2, are the previous
  changes. Item 3 is this one.
- Contested notes. `capture_note` accepts optional `contests` (existing slugs)
  and files a new inbox note with `status: contested` plus the evidence in the
  body. Optional lifecycle values on a new note are `active`, `stale`, and
  `archived`. Notes that omit `status` are unchanged, and there is no migration
  that rewrites them. `propose_resolution` files a second inbox note
  (`resolution: proposed`) for a human to approve. The same `origin_ref`
  returns the note already filed. `get_index` lists contested notes first.
  Search hits include `status`, and contested hits include `contests`.
  CLI: `python3 scripts/resolve_contest.py` (dry-run unless `--apply`).
  Skill: `skills/memex-resolve`.
- LoCoMo and Tekmen-eval runner (`scripts/eval_arms.py`). Three arms: model
  only, librarian harness with no notes, harness plus Memex retrieval.
  Default model is a mock (no network). `--model live` uses
  `MEMEX_MODEL_URL` (OpenAI-compatible local endpoint). `--allow-remote` is
  the switch that may call a hosted provider. LoCoMo is fetched with
  `--fetch` into `~/.cache` (the dataset is not in the repo) and scored
  with the public token-F1 / abstain methodology, reported per category
  with median retrieval latency and retrieved tokens. Tekmen-eval reads a
  question file from outside the repo (`--questions` or `TEKMEN_EVAL_PATH`);
  the committed file is a synthetic shape example. Arm C writes the local
  meter (`eval.locomo` or `eval.tekmen`) and fills `hit`.
  `scripts/guard_private_eval.py` rejects a vendored `locomo10.json` or a
  private question file. See `docs/evals.md`.

- `scripts/setup_agent_sandbox.sh` — one-command Lane A/B bootstrap for any
  sandbox (NemoClaw/OpenShell or plain container): vault clone/copy + all eight
  skills + optional in-sandbox memexlab-mcp venv; dry-run by default, JSON event,
  idempotent for existing vaults. 5 tests + simulated-sandbox e2e.

- MCP client guide: NVIDIA NemoClaw / OpenShell section — two lanes (skills-native
  OpenClaw; in-sandbox stdio memexlab-mcp with the managed-MCP HTTPS-only caveat),
  runtime-vs-memory governance composition note.

- `memex reindex` + `memex search --mode hybrid` — the local reproducible
  semantic index: derived cache in `.memex/embeddings/` (content-hash
  invalidation, byte-identical rebuilds, `--verify` CI check), embedding
  provider resolution local-first (`MEMEX_EMBED_URL` → GLM `embedding-3` →
  OpenAI), hybrid BM25+cosine ranking that refuses on a stale index. Keyword
  mode stays the default and never needs a provider. 8 tests.

- `scripts/run_benchmark.py` — executable benchmark runner for the sample query
  set: recall@k / MRR through the real `memex search` surface (JSON report,
  `--min-recall` CI gate). Baseline on the fake vault: recall@5 = 1.00,
  MRR = 0.67 — the floor RFC-005's hybrid retrieval must beat.
- `scripts/ingest_transcript.py` — deterministic .vtt/.srt/.txt meeting-transcript
  ingester (speaker turns as timestamped quotes, content-hash dedup).

- `memex qa` — the CLI's first model-touching command: BM25-retrieved,
  `[[slug]]`-cited answers with a deterministic post-flight citation lint
  (counts in every JSON event; `--strict` gates), provider resolution
  local-first (`MEMEX_MODEL_URL` → GLM `glm-5.2` → Anthropic → OpenAI, env
  only, zero markup), five lens presets as overridable files, `--view`
  scoping, `--apply` files answers into `_qa/`. 8 tests.

- `memex view` + `memex search` — read-only retrieval in the CLI with the exact
  semantics of the MCP server: views-as-files (`views/*.md`, strict `query:`
  block) and deterministic BM25 with `[[slug]]`-citable results; `--view` scopes
  a search, `--format json` for scripting. 3 tests.
- `docs/capture-anywhere.md` — one-gesture capture on every device: the CLI path,
  a zero-install Obsidian bookmarklet, a 5-step iOS share-sheet Shortcut recipe,
  and the Android share-target path; extension deliberately deferred with the
  criterion written down.
- `memex ingest youtube` — published captions → transcript note with 60-second
  timestamp heading anchors (`{#105}`) and `?t=` deep links; uploaded-over-auto
  track selection, `--lang`, honest no-caption-data failure. 8 tests.

- `memex-cli/` — the `memex` CLI package, built from scratch starting with the
  ingest spine: `memex ingest url` (local readable-markdown extraction, provenance
  frontmatter, idempotent re-capture via `.memex/ingest_state.json`, dry-run by
  default, one JSON event per invocation). 6 tests.
- `memex ingest kindle` — deterministic My Clippings.txt importer: one note per
  book, append-only re-imports (user edits survive), bookmarks dropped. 7 tests.
- `memex ingest readwise` — incremental Readwise export importer (env-only token,
  cursor in ingest state, exact id-based idempotency, append-only). 7 tests.
- `memex ingest rss` — stdlib RSS 2.0/Atom puller: incremental per feed,
  volume-guarded (--limit, default 20), --since filter, HTML-stripped summaries.
  8 tests.
- `memex ingest youtube-feed` + `memex ingest feeds` — YouTube channels via the
  official public RSS endpoint (UC id / channel URL / @handle resolution), and a
  `feeds.md` subscriptions file (tags per line, per-source failure isolation).
  6 tests.
- `docs/mcp-clients.md` — Connecting Agents (MCP) guide in the docs nav; supersedes
  the earlier `docs/engineering/mcp-clients.md` (removed, index link updated).
- `scripts/ingest_ics.py` — deterministic, stdlib-only calendar-invite ingester
  (one meeting note per VEVENT into `inbox/`, UID-deduplicated, dry-run default).
- Agent-readable docs: `docs/llms.txt` (index of every page's raw markdown) and
  `docs/llms-full.txt` (full manual in one file), generated by
  `scripts/build_llms_txt.py` (dry-run by default, `--apply` writes, `--check` for CI).
- `docs/vault-sync.md` — git-based vault sync guide: `.gitignore` policy, the
  private-remote sovereignty ladder, mobile paths, conflict hygiene, secrets
  discipline, and a two-device walkthrough.
