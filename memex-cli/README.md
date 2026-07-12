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

## Contract

Same invariants as the whole engine: the filesystem is the database, plain markdown
is the storage layer, dry-run is the default for every mutation, and the LLM is
additive — this package uses no model at all.

## Roadmap (shared ingest spine)

`ingest kindle` / `ingest readwise` (highlight importers), `ingest rss` /
`ingest youtube-feed` (feeds), `ingest youtube` (transcripts with timestamp
anchors) — each a small module on the fetch/extract/state spine in this package.
