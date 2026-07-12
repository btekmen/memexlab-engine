# memex (memexlab-cli)

**A local-first CLI over a plain-markdown vault.** This package is being built from
scratch, ingest spine first: capture sources into your vault's `inbox/` with
provenance — dry-run by default, no cloud, no account, no LLM in the capture path.

Part of [MemexLab](https://memexlab.xyz); pairs with
[`memexlab-mcp`](../memexlab-mcp/) (the governed MCP server over the same vault). MIT.

## Install / run

```bash
uvx --from "git+https://github.com/btekmen/memexlab-engine#subdirectory=memex-cli" \
  memex --help
```

> Not on PyPI yet; once `memexlab-cli` is published this becomes `uvx memexlab-cli`.

## Commands

### `memex ingest url <URL>`

Fetch a public page, extract readable markdown locally (trafilatura), and file it
into the vault's write dir (default `inbox/`, configurable via `write_dir:` in the
vault's `governance.yml`) with provenance frontmatter:

```bash
memex ingest url https://example.com/essay --vault ~/vault            # dry-run preview
memex ingest url https://example.com/essay --vault ~/vault --apply    # write the note
```

- **Dry-run by default** — `--apply` is explicit (universal contract).
- **Idempotent** — a URL you already captured is skipped (`--force` re-captures);
  the cursor lives in `.memex/ingest_state.json`, a rebuildable cache, never truth.
- **Provenance** — `source_url`, `captured_via: cli`, `captured_at`, author/date when
  the page declares them.
- **One JSON event per invocation** on stderr; exit `0`/`1`.
- **Honest capture** — what a local fetch can't see (heavy JS, paywalls) is not
  captured; we never proxy through a cloud renderer.

### `memex ingest kindle <My Clippings.txt>`

Deterministic importer for Kindle highlights — no network, no LLM:

```bash
memex ingest kindle "~/My Clippings.txt" --vault ~/vault          # dry-run plan
memex ingest kindle "~/My Clippings.txt" --vault ~/vault --apply  # write/append
```

- **One note per book** in the write dir; highlights as quoted blocks with
  page/location/date refs; Kindle notes rendered as **Note.** blocks; bookmarks
  dropped.
- **Idempotent & append-only** — highlight identity is (book, location, text);
  re-imports append only what's new and never rewrite the note, so your own
  edits to the book note survive.
- Handles BOM/CRLF and page-only or location-only variants.

### `memex ingest readwise [--since ISO]`

Incremental import from the Readwise export API — the vault is the hub; Readwise is
an upstream source we import *from*:

```bash
export READWISE_TOKEN=...   # environment only — never in a file
memex ingest readwise --vault ~/vault           # dry-run plan (full export first run)
memex ingest readwise --vault ~/vault --apply   # write/append; cursor advances
```

- **Incremental** — the cursor lives in `.memex/ingest_state.json`; `--since`
  overrides it. First run imports the full export.
- **Exact idempotency** — highlight identity is Readwise's own id; append-only, so
  your edits to a note survive re-import.
- Same note shape as the Kindle importer (one note per source, provenance
  frontmatter incl. `readwise_id`, `source_url`, category).

### `memex ingest rss <feed-url> [--limit N] [--since ISO]`

Pull one RSS/Atom feed into the write dir — feeds without a cloud; cron it yourself
(there is deliberately no daemon):

```bash
memex ingest rss https://example.com/feed.xml --vault ~/vault             # dry-run
memex ingest rss https://example.com/feed.xml --vault ~/vault --apply     # write
```

- **Incremental per feed** (item identity = guid/id) via `.memex/ingest_state.json`.
- **Volume-guarded** — `--limit` (default 20) so a flooding feed can't bury `inbox/`;
  held-back items surface on the next run. `--since` drops older items.
- Note body = the summary the feed provides; deep-capture a specific item with
  `memex ingest url`. Stdlib-only parsing (RSS 2.0 + Atom), HTML stripped.

### `memex ingest youtube-feed <channel>` · `memex ingest feeds`

Follow YouTube channels through their **official public RSS endpoint** (no API key,
no scraping) — `UC…` id, `/channel/` URL, or `@handle` all resolve:

```bash
memex ingest youtube-feed @somechannel --vault ~/vault --apply
```

Keep all subscriptions in the vault itself — `feeds.md`, one per `- ` line, `#tag`
tokens become default tags — and pull everything at once:

```markdown
- https://example.com/feed.xml #ai #research
- @somechannel #video
```

```bash
memex ingest feeds --vault ~/vault --apply    # cron this; one bad feed never stops the rest
```

### `memex view [name]` · `memex search <query> [--view NAME]`

Read-only retrieval, identical semantics to the MCP server (same view format,
same deterministic BM25):

```bash
memex view --vault ~/vault                       # list saved views (views/*.md)
memex view memory-notes --vault ~/vault          # a view's member notes
memex search "governed memory" --vault ~/vault   # [[slug]]-citable hits
memex search "banking" --view memory-notes ...   # search inside a view
```

Views are notes (`views/<name>.md`, `type: view` + a strict `query:` block —
unknown fields are errors); sharing a view = sharing the file. `--format json`
on both commands for scripting.

### `memex qa "<question>"` — the one command that touches a model

A `[[slug]]`-cited answer over your vault. **The citation contract is checked,
not hoped**: every citation must resolve to a note that was actually in the
model's context; the counts land in the JSON event, and `--strict` exits 1 on
any violation.

```bash
export GLM_API_KEY=...                    # or MEMEX_MODEL_URL / ANTHROPIC_API_KEY / OPENAI_API_KEY
memex qa "what do my notes say about governed memory?" --vault ~/vault
memex qa "..." --view banking --lens keypoints          # scoped + shaped
memex qa "..." --lens translate --lang tr --apply       # file into _qa/
```

- **Provider resolution (env only, zero markup):** `MEMEX_MODEL_URL` (any
  OpenAI-compatible local endpoint — the sovereign route, no key) →
  `GLM_API_KEY` (default `glm-5.2`) → `ANTHROPIC_API_KEY` (`claude-sonnet-5`) →
  `OPENAI_API_KEY`. `MEMEX_MODEL` overrides the model on any route. No key, no
  endpoint → clean refusal: qa needs a model; nothing else here ever does.
- **Retrieval** is the same deterministic BM25 as `memex search`; `--view`
  scopes it, `--include` pins slugs.
- **Lenses are files:** `--lens keypoints | eli5 | translate | counter |
  actions` — built-ins ship in the package; a `lenses/<name>.md` in your vault
  overrides by name.
- Answer to stdout by default; `--apply` files it into `_qa/` with frontmatter
  (`type: qa`, `cited_slugs`, `model`, `lens`).
### `memex ingest youtube <video-url> [--lang CODE]`

Capture a video's **published captions** as a transcript note with timestamp
heading anchors — cite the exact minute (`[[note#105]]`), jump back via the
`?t=` deep link on every anchor:

```bash
memex ingest youtube https://youtu.be/VIDEO --vault ~/vault --apply
```

- 60-second anchor buckets: `## [1:05](https://youtu.be/ID?t=65) {#105}`.
- Uploaded captions preferred over auto-generated; `transcript_kind:` frontmatter
  records which you got. `--lang` picks a specific track.
- **Honest capture:** public caption endpoints only — no account, no scraping
  behind auth. YouTube withholds timedtext for some videos/regions on
  non-browser clients; when that happens we fail with a clear message instead
  of guessing. An explicit opt-in local-ASR path is future work.

### `memex reindex` · `memex search --mode hybrid`

An optional, **local, reproducible** semantic layer — the index is a derived
cache under `.memex/embeddings/`, rebuildable from the vault at any time
(delete it; nothing is lost but compute):

```bash
export MEMEX_EMBED_URL=http://localhost:8080/v1   # or GLM_API_KEY / OPENAI_API_KEY
memex reindex --vault ~/vault                     # staleness plan (dry-run)
memex reindex --vault ~/vault --apply             # embed changed/new notes
memex reindex --vault ~/vault --verify            # CI check: exit 1 if stale
memex search "vague memory of that idea" --mode hybrid --vault ~/vault
```

- Content hashes invalidate exactly the notes that changed; deleted notes drop
  out; same vault + same model ⇒ byte-identical index (tested).
- Hybrid = normalized BM25 + cosine, fixed 0.5/0.5 — and it **refuses on a
  stale index** so rankings stay reproducible. Keyword mode remains the
  default and needs no provider, ever.

## Contract

Same invariants as the whole engine: the filesystem is the database, plain markdown
is the storage layer, dry-run is the default for every mutation, and the LLM is
additive — this package uses no model at all.

## Roadmap (shared ingest spine)

`ingest kindle` / `ingest readwise` (highlight importers), `ingest rss` /
`ingest youtube-feed` (feeds), `ingest youtube` (transcripts with timestamp
anchors) — each a small module on the fetch/extract/state spine in this package.
