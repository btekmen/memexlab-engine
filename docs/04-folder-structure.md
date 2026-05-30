# Folder Structure

Seven top-level folders under the vault root, plus two hidden directories for machine state and a root-level set of core notes. Nothing else belongs at the vault root.

```
<your-vault>/  <your-name>.md       ← core note (persona)  memexlab.md        ← core note (homepage)  README.md              ← optional, human-readable vault guide  inbox/                 ← quick capture  raw/                   ← ingested source text  wiki/                  ← canonical atomic notes  people/                ← curated — people  companies/             ← curated — companies  philosophies/          ← curated — stances / worldviews  eras/                  ← curated — temporal frames  projects/              ← active, goal-oriented work  archive/               ← retired content (read-only)  templates/             ← Obsidian Templater files  _qa/                   ← Q&A outputs (engine-written)  _index/                ← structured index outputs  _essays/               ← essay outputs  _slides/               ← slide-deck outputs  _charts/               ← chart PNGs + sidecar notes  _lint/                 ← lint reports  .obsidian/             ← Obsidian workspace config  .memex/                ← engine state: snapshots, log.jsonl
```

## Core notes (vault root)

Purpose. System anchors. Core notes are pinned context for every LLM-driven mode (compile, qa, index, essay, slides). They describe who the operator is (`<your-name>.md` — persona) and what the system is about (`memexlab.md` — homepage).

Rules. - Two files only. Adding a third requires editing `Vault.CORE_WHITELIST`. - Both carry `CoreFrontmatter` (not Atomic or Curated). - Never moved out of the root. - Never deleted. - Never contain transient content — they are slowly-changing anchors.

Why it matters. Every retrieval prepends these two notes to the LLM context, so they influence every output. Keep them sharp and short.

## inbox/

Purpose. Free-form capture. The first destination for anything you don’t want to forget.

Belongs. Pasted URLs, unedited transcripts, half-formed thoughts, meeting notes that need triage, loose quotes, open tabs you want to read later.

Does not belong. Finished thinking. Anything you want to link to. Anything you plan to keep for more than a week.

Naming. `YYYY-MM-DD-HH-MM-short-description.md` — or whatever your Obsidian capture template produces. The linter ignores this folder.

Retention. Triaged at the weekly review. A clean inbox at Friday close is the goal.

## raw/

Purpose. Canonical storage of ingested source text.

Belongs. One file per source, full text included. Articles, papers, reports, transcripts, internal memos from <your-company> or <your-product>, personal correspondence if it’s relevant to the knowledge work.

Does not belong. Anything derivative. An LLM summary of a paper is not a raw source — the paper itself (verbatim) is. Your notes about a paper are atomic wiki notes, not raw notes.

Naming. `YYYY-MM-DD-publisher-short-title.md`. Date is the ingestion date, not the publication date (publication date lives in frontmatter).

```
Example. raw/2026-03-17-bloomberg-stablecoin-settlement-rails.md, raw/2025-11-04-imf-wp-cbdc-interop.md, raw/2026-02-10-<your-company>-internal-memo-q1.md.
```

Frontmatter. `CuratedFrontmatter` with `type: source` (or `paper`, `transcript`, `memo`). Include `source_url`, `author`, `publication_date`, `publisher`.

Do not edit. Treat raw files as immutable. Fix typos by regenerating from the source; do not rewrite.

## wiki/

Purpose. Atomic canonical notes — the durable knowledge layer.

Belongs. One concept, one claim, or one pattern per note. 200–1200 words. Links to related concepts and citations back to raw sources.

Does not belong. Summaries of whole books or papers (those are multiple atomic notes after compilation). Questions (use `wiki/questions/` or a dedicated tag). Project-specific write-ups (those are outputs or project notes).

Naming. `slug-form-of-title.md`. Slugs are lowercase, hyphenated, ASCII-transliterated from Turkish. `"Anlık Mutabakat"` → `anlik-mutabakat`.

Frontmatter. `AtomicFrontmatter` with `type: article`.

Sub-structure. The folder is flat by default. Some themed sub-folders are acceptable when they carry clear meaning:

- `wiki/questions/` — open research questions.

- `wiki/claims/` — short, testable claims distinct from conceptual articles (optional; only if you commit to maintaining the distinction).

Do not create sub-folders per domain (no `wiki/stablecoins/`). Domains are tags, not folders.

## people/, companies/, philosophies/, eras/ (curated ontology)

Purpose. Entity hubs. One note per real-world entity.

Belongs. A short biography or description, links to every relevant atomic note, links to every raw source by that author / about that entity, the entity’s current status (active, inactive, dissolved) where relevant.

Does not belong. Multiple entities in one note. A fictitious entity (real-world only — characters go in `wiki/` if at all).

Naming. `<slug>.md`. For people, `firstname-lastname.md` (`garry-tan.md`). For companies, `<slug>.md` (`<your-company>.md`, `<your-product>.md`). For philosophies, the name of the stance (`islamic-finance.md`, `full-reserve-banking.md`). For eras, a dated label (`post-2008-basel-era.md`, `early-stablecoin-era-2019-2024.md`).

Frontmatter. `CuratedFrontmatter` with the appropriate `type`.

Why a whole ontology. Entities are the stable fixed points of your corpus. Articles come and go; people and companies persist for decades. Giving them first-class notes means every downstream reference is a link, not a string match.

## projects/

Purpose. Active, goal-oriented work with a start, end, and deliverables.

Belongs. One folder per project. Inside each folder: `index.md` (the project root), `notes/` (project-local scratch), `outputs/` (project-specific deliverables).

Does not belong. Always-on concerns (those are wiki notes or their own ontology entry). Completed projects (those move to `archive/`).

Naming. `YYYY-<project-slug>/`. The year prefix keeps related projects grouped and makes the archive readable.

Example.

```
projects/  2026-stablecoin-settlement-whitepaper/    index.md    notes/      interview-central-bank-operator.md      regulatory-timeline.md    outputs/      whitepaper-v1.md      v1-slides.md  2025-<your-company>-platform-strategy-refresh/    index.md    notes/    outputs/
```

Lifecycle. Each project has a dated end. When closed: promote durable insights to `wiki/`, move the folder to `archive/projects/YYYY-<slug>/`, update the project’s `index.md` with a one-paragraph retrospective.

## archive/

Purpose. Retired content that is too valuable to delete and too stale to live in the active vault.

Belongs. Closed projects, deprecated concept notes (replaced by better ones), ingested sources later judged unreliable (kept with an explanatory note), old daily notes older than a rolling window.

Does not belong. Active content. Drafts. Anything you might want to edit.

Rules. - Read-only by convention. - Never linked to from active notes (outgoing links into the archive are tolerated only for citation purposes when an older-self’s position is being discussed). - Excluded from `memex lint` (the linter skips it by default) and from output retrieval (no essay retrieves from the archive).

Structure. Mirror the top-level structure for clarity:

```
archive/  projects/    2025-early-islamic-finance-explorer/  wiki/    deprecated-atomic-settlement-definition.md  raw/    2022-stablecoin-article-since-contradicted.md
```

## templates/

Purpose. Obsidian Templater files.

Belongs. One template per note type: `source.md`, `paper.md`, `transcript.md`, `concept.md`, `person.md`, `company.md`, `philosophy.md`, `era.md`, `project.md`, `memo.md`, `slides.md`, `daily-note.md`.

Does not belong. Actual content. Templates are skeletons — they produce notes, they are not notes themselves. The linter excludes this folder.

See. `05-templates.md` for each template’s shape.

## _qa/, _index/, _essays/, _slides/, _charts/, _lint/ (output folders)

Purpose. Engine-written outputs.

Belongs. Only what the engine puts there. Each folder corresponds to a CLI command (`qa` → `_qa/`, `index` → `_index/`, etc.).

Does not belong. Anything you write by hand. If you want to write an essay manually, put it in `wiki/` or a project folder. The underscore prefix marks these folders as machine-owned.

Naming. Deterministic, slug-based. The engine generates filenames; operators do not.

```
Example outputs. - _qa/qa-2026-04-19-does-the-gcc-adopt-wholesale-cbdc-by-2028.md - _index/index-topic-stablecoin-settlement.md - _essays/essay-the-case-for-deferred-net-settlement.md - _slides/slides-programmable-money-primer.md - _charts/chart-tag-frequency-2026-04-19.png - _charts/chart-tag-frequency-2026-04-19.md (the sidecar) - _lint/lint-2026-04-19.md
```

## .obsidian/ and .memex/

Machine state, not content.

`.obsidian/` — Obsidian workspace, plugins, hotkeys. Version-control only if you care about reproducing your workspace on another device.

`.memex/` — engine state: - `snapshots/<id>/` — file copies made before each `--apply` run of `migrate` or `compile`. Used by `memex rollback`. - `log.jsonl` — append-only JSON event log from every engine invocation.

Both are excluded from the linter, from output retrieval, and from Obsidian’s default index (most Obsidian setups ignore dotfolders by default).

## Naming conventions summary

Layer

Convention

Inbox

```
YYYY-MM-DD-HH-MM-short-desc.md
```

Raw

```
YYYY-MM-DD-publisher-short-title.md
```

Wiki

```
slug-form-of-title.md
```

People

```
firstname-lastname.md
```

Companies

```
<slug>.md
```

Philosophies

```
<stance-slug>.md
```

Eras

`<slug>-YYYY-YYYY.md` (date range at end)

Projects

```
YYYY-<project-slug>/
```

Outputs

engine-generated, deterministic

All slugs are lowercase, hyphenated, ASCII-transliterated. Turkish `İ` → `i`, `ı` → `i`, `ş` → `s`, `ğ` → `g`, `ü` → `u`, `ö` → `o`, `ç` → `c`. The engine’s `slugify` helper handles this consistently.

---

[← Core Concepts](03-core-concepts.md) · [Docs index](README.md) · [Daily Workflow →](05-daily-workflow.md)
