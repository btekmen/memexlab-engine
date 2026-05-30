# Glossary

Alphabetical definitions of every term used in these docs with a specific, non-obvious meaning. Terms used only in their ordinary English sense are not listed.

• • •

Apply. The second phase of any mutating engine command. Preceded by a dry-run. Invoked with `--apply`. Writes the planned changes to disk. Every `--apply` of `migrate` or `compile` takes a snapshot first.

Archive. The vault folder (`archive/`) where content that no longer earns active space moves. Move-to-archive is preferred over deletion for anything that had inbound links or was referenced in a finished output.

Atomic note. A single-concept note in `wiki/`. One idea, one file, one slug, linkable and reusable. Distinct from a raw source (which may span many concepts) and from a project note (which is goal-scoped).

AtomicFrontmatter. The schema applied to notes in `wiki/`, `_qa/`, `_index/`, `_essays/`, `_slides/`, `_charts/`, `_lint/`. Required fields: `date`, `type`, `status`, `tags`, `latticework`. Optional: `title`, `source`. See `06-metadata-and-tagging.md`.

AtomicType. The controlled vocabulary for an atomic note’s `type:` field: `article | qa | lint | index | essay | slides | chart`.

Backfill. A migration pattern that adds a missing field to existing notes with a default value — e.g., `backfill_latticework` adds `latticework: []` to curated notes missing the field.

BM25. The deterministic retrieval algorithm used by the engine. Ranks notes by term overlap with the query, with standard document-frequency weighting. Implemented in `memex.retrieval.bm25`.

Capture. The first step in the eight-step flow — fast, unstructured, low-friction note-taking into `inbox/`. No decisions made at capture time.

Canonical note. A wiki note that has reached `status: evergreen` — re-read, re-validated, expected to stand for years. The most trust-bearing content in the vault.

Chart. An engine-generated PNG + sidecar markdown note summarising a slice of vault metadata (tag frequency, type distribution, latticework coverage, timeline). Produced by `memex chart`.

Compile. The LLM-driven step that turns a raw source into candidate atomic notes. Invoked by `memex compile`. Always dry-run first, apply second. See `04-daily-workflow.md` step 4.

Compounding. The value growth pattern the vault is designed for. A single day’s work looks trivial; a year’s work looks like infrastructure. The gap is where most knowledge systems fail.

CoreFrontmatter. The schema applied to the two root-level core notes (`<your-name>.md`, `memexlab.md`). `type:` restricted to `persona | homepage | manifest`. Changes to core notes should be rare.

Core notes. The two vault-root notes always included in every LLM retrieval. Ground the model in who you are and how the vault works. See `09-onboarding.md` step 4.

CuratedFrontmatter. The schema applied to notes in `people/`, `companies/`, `philosophies/`, `eras/`, `raw/`, `projects/`. Required fields: `title`, `type`, `created`, `updated`, `status`, `tags`, `latticework`.

Dataview. An Obsidian plugin that queries notes by frontmatter inside the editor. Useful for in-vault filters; not required by the engine.

Decay. The default state of any information system over time: schema drift, broken links, duplicates, stale ontology. Maintenance is the active countering of decay.

Deterministic. A property of the engine’s non-LLM modes: given the same vault and same inputs, they produce identical outputs. `doctor`, `migrate`, `rollback`, `lint`, and `chart` are deterministic. `compile`, `qa`, `index`, `export *` are not (LLM-driven).

Draft (status). The middle maturity tier. A note that’s been re-read, edited for clarity, and link-verified, but hasn’t yet earned evergreen status.

Dry-run. The default mode of any mutating engine command. Prints the plan; exits without modifying the vault. The system’s core safety contract.

Engine. The `memex` Python CLI. Ten command modes, all sharing a common contract (dry-run-first, atomic writes, snapshots, structured logging).

Entity note. A curated note representing a person, company, philosophy, or era. One file per entity. The ontology layer.

Evergreen. The highest maturity tier for an atomic note. Re-validated weeks or months after creation; expected to stand for years. See `10-best-practices.md` for promotion criteria.

Export. Engine modes that produce finished outputs. `export essay` and `export slides` are the current set.

Feedback loop. The eighth step of the workflow. Using an output surfaces gaps; filling those gaps improves the vault; the next output is better. The mechanism by which the vault compounds.

Flat-wiki convention. All atomic notes live directly in `wiki/`, not in subfolders. Keeps slugs globally unique and simplifies retrieval.

Frontmatter. The YAML block at the top of every note. Schema-validated. Invalid frontmatter is an error, not a warning.

Gaia. A Marp theme (`--theme gaia`) used by `memex export slides` for a particular visual style. One of several Marp presets.

Graph. The link structure across all notes. Built from `[[wiki-links]]`. Obsidian’s graph view visualises it; the engine’s retrieval layer uses it.

Harness. The engine’s test infrastructure plus the eval vault used to test prompt changes. A harness run is how a behaviour regression is caught before it ships.

Hallucination. An LLM-produced claim that is not supported by the source or context. Caught by human review of compile and export output before `--apply`.

Inbox. The fast-capture folder (`inbox/`). Weekly review promotes, merges, or deletes every item. A non-empty inbox for more than a week is a decay signal.

Index. An engine mode (`memex index`) that produces a structured note over a topic in one of five flavours: `topic`, `reading-order`, `concept-map`, `category`, `problem-view`.

Ingest. The step that promotes an inbox item into a raw source — fetch full text, fill frontmatter, file under `raw/` with proper filename.

Islamic finance. One of the domains the vault is tuned for. Compatibility considerations for programmable money under Islamic finance principles (Sharia-compliant settlement structures, profit-and-loss sharing) recur across this vault’s running examples.

JSONL. The newline-delimited JSON format used by the engine’s structured log (`.memex/log.jsonl`). Append-only, grep-friendly.

Latent knowledge. Knowledge that exists in the vault’s content but isn’t directly stated. Retrieval + LLM generation is how latent knowledge becomes explicit.

Latticework. <your-name>’s personal framing: five problems (seeing reality, deciding under uncertainty, allocating time and energy, avoiding self-deception, playing long games) that serve as the meta-taxonomy for atomic notes. The `latticework:` frontmatter field tags which problems a note addresses.

Lint. The deterministic validation mode (`memex lint`). Five checks: frontmatter validity (error), broken wiki-links (error), orphan atomic articles (warn), stub bodies (info), missing latticework on curated (info). Fails the run on any error finding.

LLMClient. The single class in `memex.llm` through which all LLM calls route. Implements retries, structured output parsing, logging, error handling.

Log. The engine’s structured event log at `.memex/log.jsonl`. One JSON event per command invocation and per LLM call. Grep it to answer “did anything go wrong this week?”

Manifest. The `type:` of the system core note (`memexlab.md`). Describes how the vault works; grounds every LLM call.

Marp. A markdown-to-slides renderer. The engine’s `export slides` output is Marp-compatible (`marp: true` in frontmatter).

MCP. Model Context Protocol — an unrelated term from tooling infrastructure; not used by this engine. Listed here only because the term appears in the broader ecosystem and might be sought.

Memex. This engine (`memex`), and also the name of the conceptual lineage (Vannevar Bush’s “memex” from As We May Think, 1945). MemexLab is the specific instance.

Migrate. The engine mode (`memex migrate`) that brings existing notes forward when the schema changes. Always dry-run by default; always snapshots before apply.

Ontology. The vault’s curated entity layer — people, companies, philosophies, eras. One file per entity. Updated by the owner, not auto-generated.

Open question. A note in `wiki/questions/` representing a research question you haven’t yet answered. Tagged `open-question`. Compounds as a research agenda.

Orphan. An atomic note with zero inbound links. Surfaced as a warning by `memex lint`. Investigate each — link, merge, or archive.

Output. An engine-generated file under one of the underscore-prefixed folders (`_qa/`, `_index/`, `_essays/`, `_slides/`, `_charts/`). A first draft, not a finished artifact.

Persona. The `type:` of the personal core note (`<your-name>.md`). Describes who you are; grounds every LLM call.

Problem-1 through problem-5. The five Latticework problem identifiers used in the `latticework:` frontmatter field. See Latticework.

Process. The step between ingest and compile — reading the raw source, annotating it, deciding whether to compile. Not automated.

Programmable money. One of the domains the vault is tuned for. Smart-contract-enabled monetary instruments, including stablecoins, CBDCs, and embedded-finance rails.

Project. A goal-driven workspace (`projects/<slug>/`) with an end date and a defined deliverable. Distinct from wiki (open-ended themes).

Promotion. Moving a note up the status ladder: `seed` → `draft` → `evergreen`. Always manual. See `10-best-practices.md`.

Prompt files. The system prompts under `prompts/`, one file per LLM-driven mode. Version-controlled alongside the engine. Edits change engine behaviour on the next run.

QA. The engine mode (`memex qa`) that answers a question against the vault. Produces an answer note in `_qa/` with inline `[[slug]]` citations.

Raw. The `raw/` folder, containing ingested sources with citation metadata. Wiki notes cite raw notes via `source:` frontmatter.

Retrieval. The layer that picks which notes to include in an LLM call’s context. BM25-based, deterministic, shared across all LLM-driven modes.

Rollback. The engine mode (`memex rollback`) that restores a snapshot. The inverse of `migrate --apply`.

Schema. The Pydantic models in `memex/schemas.py` that define valid frontmatter. Three schemas: Atomic, Curated, Core. Schema changes go through `migrate`.

Seed (status). The lowest atomic-note maturity tier. Body exists; links may be thin; hasn’t been re-read. The default on compile.

Skill file. A prompt file under `prompts/` — a set of model-level instructions that guide one engine mode. The term borrows from broader ecosystem usage; here it specifically means the contents of `prompts/`.

Slug. The lowercase, hyphenated identifier of a note. The filename stem. Stable across title changes. Used for linking (`[[slug]]`) and for matching in retrieval.

Snapshot. A pre-apply copy of every file a mutating command will change, written to `.memex/snapshots/<id>/` with a `manifest.json`. Enables clean rollback.

Source. A raw file in `raw/` that an atomic note cites via the `source:` frontmatter field.

Stablecoin settlement. One of the domains the vault is tuned for. The tradeoffs between gross and net settlement as applied to stablecoin rails, with implications for float, liquidity, and systemic risk.

Status. The maturity field on every note. Atomic: `seed | draft | evergreen`. Curated: `seed | draft | active | evergreen`. Never auto-transitioned.

Stub. An atomic note with a very short body, created to satisfy a wiki-link. Flagged by the linter as an info finding. Develop into a real note when the topic matters; delete if it doesn’t.

Structured output. An LLM response parsed into a Pydantic schema. Every LLM call in the engine uses structured output; parse failures are retried once, then surfaced as `LLMOutputError`.

Tag. A slash-namespaced classifier in the `tags:` frontmatter field — `topic/stablecoin`, `geo/turkey`, etc. Second-class to wiki-links; used for cross-cutting dimensions that don’t warrant their own entity.

Template. A Templater-executed frontmatter-plus-skeleton file under `templates/`. Applied automatically by Obsidian folder mapping. Never hand-type frontmatter.

Templater. An Obsidian plugin that runs scripted templates. Required by this system’s workflow.

Transcript. A raw-source `type:` for captured speech — interview, meeting, voice memo. Full verbatim text in the body.

Type. The most strictly-validated frontmatter field. Controlled vocabulary per schema; folder-dependent. Adding a new type is a schema change.

Vault. The top-level folder (recommended: `~/Documents/Obsidian/<your-vault>/`) containing everything: core notes, inbox, raw, wiki, ontology, projects, archive, templates, outputs, `.memex/`. The filesystem is the database; the vault is the database.

Wiki. The canonical-note folder (`wiki/`). Atomic notes, one concept per file. The vault’s most load-bearing content.

Wiki-link. A link of the form `[[slug]]` connecting one note to another. The primary mechanism for building the graph.

YAML. The format of all frontmatter. Schema-validated. Unknown keys are rejected.

---

[← Maintenance Checklist](maintenance-checklist.md) · [Docs index](README.md)
