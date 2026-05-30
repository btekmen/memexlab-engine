# Core Concepts

Precise vocabulary matters. Every term below has a single, non-overlapping meaning in this system. If two concepts share a word, one of them is using the wrong word.

## Source note

A file in `raw/` that holds the full, verbatim text of an external source. Frontmatter records where it came from (URL, citation, author, date ingested). A source note is never edited after ingestion except to correct frontmatter. It is the reproducibility anchor for every downstream atomic note that cites it.

Example. `raw/2026-02-10-bis-working-paper-no-1112.md` holds the full PDF-extracted text of a Bank for International Settlements working paper on CBDC interoperability.

## Canonical note

A note in the wiki layer — either an atomic note in `wiki/` or an ontology entry in a curated folder (`people/`, `companies/`, `philosophies/`, `eras/`). Canonical notes are the durable, linked corpus. They are the unit of retrieval. They are the input to every output.

Property. Every canonical note is supposed to outlive its individual sources. A concept page on “pre-funded settlement rails” stays useful long after the specific Bloomberg article that first surfaced the idea has been forgotten.

## Concept page

A canonical note whose subject is an abstract idea — a pattern, a mechanism, a thesis. Concept pages live in `wiki/` with `type: article`. Titles are noun phrases, not questions: “Atomic settlement”, “Gross vs net netting”, “Permissioned stablecoin issuance”.

Do this. One concept per note. Name the note after the concept, not the source that introduced it.

Do not do this. Do not create a concept page titled “Things I learned from the BIS paper” — that is a source note, not a concept.

## Canonical entity (person, company, philosophy, era)

A note in a curated folder that represents a real-world entity. The ontology is fixed — only the types listed above exist. An entity note is a hub: biography or description up top, then links out to every concept, source, and event that involves the entity.

Example entities, across your domains. <your-company> (company), <your-product> (company), Garry Tan (person), Islamic Finance (philosophy), Post-2008 Basel Accords Era (era).

## Project page

The root note of an active project. Lives at `projects/<project-slug>/index.md`. Carries a stated goal, a deadline, a set of deliverables, and a link list to the wiki notes most relevant to the work. A project page is a lens over the wiki, not a storage location for the project’s research output — durable research is promoted back to `wiki/` when the project closes.

## Output

A file produced by an engine command: an essay, a slide deck, a chart, a Q&A note, a lint report, or a structured index. Every output is a first-class note inside the vault with its own frontmatter, searchable and linkable like any other note. Outputs are regenerable and dated.

## Feedback loop

The cycle where an output reveals a gap, a gap becomes a new wiki note, and the next output is stronger because of it. Concretely: while writing an essay on stablecoin settlement you notice the wiki has no good concept page on “deferred net settlement” even though three atomic notes reference it. You create the page. The next `memex index "settlement"` retrieves it. The next essay cites it. The vault has compounded by one concept.

## Compilation

The deliberate, model-assisted act of turning a source note into one or more atomic notes. Mechanically: `memex compile <raw-file>` sends the source text plus the two core notes (persona + homepage) to the LLM, which returns a list of candidate atomic notes. The operator reviews the plan and runs `--apply` to commit.

Compilation is where the raw-to-canonical boundary lives. Until a source has been compiled, its information is captured but not available — nothing retrieves against `raw/` directly.

## Linking

The practice of creating explicit `[[wiki-link]]`s between notes. Obsidian’s link graph is the system’s primary structure — tags are secondary, folders are tertiary.

Rules of good linking: 1. Link to canonical notes, not to outputs. 2. Link by slug (the filename without the `.md`), not by title. 3. Link forward (an atomic note references a concept) and backward where appropriate (a concept note may maintain a “Key sources” section that links down to specific raw or atomic notes). 4. Broken links are errors. The linter fails the run on a broken link.

## Linting

The deterministic health check over the vault — `memex lint`. Five checks run in one pass: frontmatter validity, broken wiki-links, orphan atomic notes, stub bodies, missing Latticework problem tags. The lint report is itself a note (under `_lint/`) so the history of vault health is preserved.

Lint is not style enforcement. It is structural enforcement. A stub note is allowed to exist briefly; the lint report lets you decide when to fix it.

## Knowledge graph

The directed graph whose nodes are canonical notes and whose edges are `[[wiki-link]]`s. Obsidian renders it visually; the engine uses `LinkGraph` to resolve references during lint and retrieval. The graph is the real structure of the vault — the folder tree is just a convenience.

## Open question

A durable research question that stays in the vault as its own note until resolved. Open questions live in `wiki/questions/` (or carry `tags: [open-question]`) and reference the atomic notes that bound the possible answers. They are the seed list for future research passes.

```
Example. wiki/questions/does-the-gcc-adopt-a-wholesale-cbdc-before-2028.md.
```

## Ontology

The fixed set of curated entity types the system recognises: `person`, `company`, `philosophy`, `era`. The ontology is deliberately small. Expanding it is a schema change — it requires editing `schemas.py`, running `memex migrate`, and updating these docs. Adding a new tag is not an ontology change; adding a new type is.

## Latent vs deterministic knowledge

Deterministic knowledge is what the vault holds explicitly — the text of every note, every frontmatter field, every link. Retrieval over deterministic knowledge is reproducible: the same query against the same vault returns the same notes.

Latent knowledge is what the LLM brings to compile/qa/index/essay/slides — the model’s training-time priors, its ability to paraphrase, summarise, or spot patterns across notes. Latent knowledge is valuable but not durable; the same prompt to a different model version produces different output.

The design rule: deterministic knowledge lives in the vault, latent knowledge lives in the model. Never commit the latent layer into the vault as if it were deterministic. If an LLM output is valuable, a human edits and confirms it, then it becomes a note. Raw LLM output inside a wiki note is an anti-pattern.

## Skill files

Reusable prompt/instruction bundles loaded by the LLM at call time. Memex ships a small set under `prompts/` (e.g. `compile.md`, `qa.md`, `index/topic.md`, `export/essay.md`). These are plain markdown files; the engine loads them via `memex.llm.load_prompt`. Editing a skill file changes the system’s behaviour on the next run — no code change required.

## Harness

The runtime glue that wraps the LLM: the `LLMClient`, retry policy, structured-output parsing, and prompt loading. The harness’s job is to make LLM calls boring and reproducible — fixed retries, backoff, typed Pydantic return shapes, JSON logging. Operators rarely touch the harness; they edit skill files instead.

## Resolvers

Small, named functions that translate between loose user input and strict internal types. The engine has a handful: `_resolve_topic_or_file` (topic string or `--file`), `validate_folder` (checks a folder name against the known scope set), `_cast_chart_kind` (narrows a validated string to a typed `ChartKind`). Resolvers are the boundary between permissive CLI input and strict downstream code.

## Diarization

The term is borrowed from speech processing, where it means “who spoke when”. In Memex it means attribution inside a note: keeping it clear which sentences are summarised from a cited source, which are your analysis, and which are LLM-generated draft text that has been accepted by a human.

In practice: - A direct quote from a source is in `> blockquote` with a `[[source-slug]]` citation at the end. - Your analysis is plain prose. - Accepted LLM draft is plain prose after human review — once accepted, it is your prose. - LLM draft not yet reviewed should not be committed to the vault at all.

Diarization is what keeps a wiki note trustworthy over time. Without it, you can’t tell what you thought in 2026 from what an external source claimed, and you can’t audit the vault for factual drift.

---

[← Architecture](02-architecture.md) · [Docs index](README.md) · [Folder Structure →](04-folder-structure.md)
