# Architecture

MemexLab is two systems in close collaboration: a vault (the human-facing markdown corpus, edited in Obsidian) and an engine (the CLI that reads and writes to the vault). Everything else — Templater, Dataview, Claude, cron — is attached to one of these two surfaces.

## The one picture

```
                              +----------------+  external sources            |     Inbox      |   quick capture  (web, email, PDFs,  ──────► |   inbox/       |   free-form, messy   meetings, books)           +--------+-------+                                       │                                       │  (triage, keep-only-the-interesting)                                       ▼                              +----------------+                              |      Raw       |   full source text                              |    raw/        |   one file per source                              +--------+-------+                                       │                                       │  memex compile <source>                                       │  (LLM: cut into atomic notes)                                       ▼                              +----------------+                              |     Wiki       |   canonical atomic notes                              |   wiki/        |   one claim/concept per file                              +---+------------+   AtomicFrontmatter                                  │  ▲                                  │  │                   memex lint ────┤  │                   memex qa   ────┤  │  feedback loop                   memex index ───┤  │  (outputs link back in)                                  │  │                                  ▼  │         +-----------+  +-----------+│+-----------+  +-----------+         | Projects  |  | _qa/      ││ _essays/   |  | _charts/  |         | projects/ |  | _index/   ││ _slides/   |  |           |         | per-folder|  | _lint/    ││            |  |           |         +-----------+  +-----------+ +-----------+  +-----------+                                     outputs (first-class notes)                              +----------------+                              |    Archive     |   retired or deprecated                              |   archive/     |   (read-only)                              +----------------+                              +----------------+                              | System/Config  |   engine state, not content                              |  .memex/       |   snapshots, log.jsonl                              |  .obsidian/    |   workspace, plugins                              |  templates/    |   Templater files                              +----------------+
```

Information flows strictly top-to-bottom on the left-hand column (Inbox → Raw → Wiki). Outputs flow out to the right, but every output node is also a note inside the vault, so it is indexable, searchable, and linkable — it is not an export.

## Layer-by-layer

### Inbox

Purpose. Fast, permissive capture. If you saw or thought something and want it off your head, it goes here.

Contents. Anything: a URL, a paragraph pasted from an article, a voice memo transcription, a scrawled outline of a meeting, a screenshot’s alt-text. Files are plain markdown with a single frontmatter field (`date`) and free-form body. No title requirements. No tagging requirements.

Lifetime. A note in the inbox is expected to live there for hours to days, not weeks. Weekly review triages every item: either promote it to `raw/` (if it has long-term value and the full source text is available or reachable), paste its useful content into an existing wiki note, or delete it.

Do this. Capture aggressively. Resist the urge to classify at capture time.

Do not do this. Never link into the inbox. Inbox notes are not references; they are temporary.

### Raw

Purpose. Canonical storage of ingested source text. A note in `raw/` is the full article, paper, transcript, or excerpt, with its own frontmatter describing where it came from. This is the layer that survives compilation — the wiki notes link back to raw notes, and the raw notes are the durable record of the source.

Contents. One file per source. Example filenames:

```
raw/2026-03-17-bloomberg-stablecoin-settlement-rails.md
raw/2025-11-04-imf-working-paper-cbdc-interop.md
raw/2026-02-10-<your-company>-internal-strategy-memo.md
```

Frontmatter. `CuratedFrontmatter` with `type: source` (or `paper`, `transcript`, `memo`). `source` URL or citation. `ingested: YYYY-MM-DD`. Entity links where known.

Lifetime. Permanent. Raw notes are never deleted once compiled; they are the reproducibility anchor.

### Wiki — the canonical layer

Purpose. The durable, linked, atomic body of knowledge. This is the layer that compounds.

Contents. One atomic note per claim, concept, person, company, philosophy, era, or problem. Schemas vary by folder:

- `wiki/` — `AtomicFrontmatter`, `type: article`. Claims and concepts.

```
people/ — CuratedFrontmatter, type: person.
companies/ — CuratedFrontmatter, type: company.
philosophies/ — CuratedFrontmatter, type: philosophy.
eras/ — CuratedFrontmatter, type: era.
```

Size. An atomic article is 200–1200 words. A curated entity note is 100–800 words. Anything longer is either an output (write an essay), a project (start a project folder), or two notes that want to separate.

Links. Every wiki note should carry at least two outbound `[[wiki-link]]`s. Zero links means the note is orphaned — the linter will flag it.

### Projects

Purpose. Active, goal-oriented work with a start, an end, and deliverables.

Shape. One folder per project under `projects/`. Inside each project folder: an `index.md` (the project’s root), a `notes/` subfolder for project-local scratch, and `outputs/` for deliverables that are project-specific and don’t need to live in `_essays/` or `_slides/` long-term.

Example.

```
projects/  2026-stablecoin-settlement-whitepaper/    index.md    notes/      interview-central-bank-operator.md      regulatory-timeline.md    outputs/      whitepaper-v1.md      v1-slides.md
```

Relationship to the wiki. A project feeds off the wiki (pulling in relevant canonical notes as context) and feeds into the wiki (every durable insight extracted from the project gets promoted to an atomic wiki note when the project ends). A retired project’s folder is moved to `archive/` — its content is preserved verbatim.

### Outputs

Purpose. Durable artefacts generated against the wiki.

Types. Essays (`_essays/`), slide decks (`_slides/`), charts (`_charts/`), Q&A notes (`_qa/`), structured indexes (`_index/`), lint reports (`_lint/`). Each is produced by a CLI command and written as a first-class note inside the vault.

Re-indexability. Outputs are searchable just like wiki notes — they have frontmatter, they link back to sources via `[[slug]]`, they carry tags. An essay about stablecoin settlement surfaces on any future BM25 search for “stablecoin settlement” alongside the atomic notes it was built from.

Regenerability. An output is a snapshot of the vault at a moment in time. Regenerating it later against a more developed wiki produces a different (usually better) result. That is the point — the vault compounds, and each output captures what you knew on the date stamped into its frontmatter.

### Archive

Purpose. Retired content that is too valuable to delete and too stale to keep in the active vault.

Contents. Old projects (moved from `projects/` when closed), deprecated concept notes replaced by better ones, ingested sources that turned out to be misinformation (kept for the record with a note explaining why).

Rules. Read-only by convention. Never edited. Never linked-to from active notes. The archive is excluded from lint and from output retrieval.

### System, config, scripts

Purpose. Machinery.

Contents.

- `.memex/` — engine state: snapshots (for `memex rollback`), `log.jsonl`, nothing else.

- `.obsidian/` — Obsidian’s workspace: plugin configs, hotkeys, graph settings. Version-controlled only if you have a reason.

- `templates/` — Obsidian Templater files, one per note type.

- The engine itself (the CLI code) lives outside the vault, under `memex/` as a sibling directory.

None of this is content; none of it participates in the knowledge graph.

## Information flow, in detail

- Capture creates a note in `inbox/`.

- Ingest (manual or scripted) promotes the inbox note to `raw/` with proper metadata, keeping the full source text.

- Compile (`memex compile <source>`) reads the raw note, sends it through the LLM, and proposes a list of candidate atomic notes. The operator reviews; with `--apply` the notes are written to `wiki/` as atomic notes, each carrying a `source` field linking back to the raw file.

- Link happens in Obsidian: every new wiki note gets explicit `[[…]]` links to the related concepts it references. The lint step will catch orphans and broken links.

- Refine is an ongoing manual pass: small edits, note splitting, retagging, promotion from `draft` to `evergreen` status.

- Output commands (`qa`, `index`, `export essay`, `export slides`, `chart`) retrieve over the wiki and write back into the output folders.

- Feedback is the final arc: insights that emerge during output generation (a gap you discovered while writing an essay, a correlation visible only in a chart) become new wiki notes.

The flow is not linear; it is a spiral. Each traversal deepens the wiki and improves the next output.

## Where the engine sits

The CLI (`memex`) is a thin coordinator. It:

- reads the configured vault,

- dispatches to one of eight modes (`doctor`, `migrate`, `compile`, `lint`, `qa`, `index`, `export`, `chart`),

- either prints a plan (dry-run) or applies changes atomically with snapshots,

- logs one JSON event per invocation to `.memex/log.jsonl`.

It never holds state between calls. There is no background process, no daemon, no cache. If you lose the engine, the vault stands; if you lose the vault, the engine has nothing to act on.

---

[← Overview](01-overview.md) · [Docs index](README.md) · [Core Concepts →](03-core-concepts.md)
