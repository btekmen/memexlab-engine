# Metadata and Tagging Rules

The frontmatter of every note is a strict contract between you and the engine. The engine’s lint, retrieval, and output machinery assume schema-valid frontmatter; invalid frontmatter is an error, not a warning. This page documents every field, every rule, and every tag convention.

## Three schemas, dispatched by folder

The vault uses three YAML frontmatter schemas. Which one applies is decided by where the note lives.

Schema

Folders

`type` values

```
AtomicFrontmatter
```

`wiki/`, `_qa/`, `_lint/`, `_index/`, `_essays/`, `_slides/`, `_charts/`

```
article | qa | lint | index | essay | slides | chart
CuratedFrontmatter
people/, companies/, philosophies/, eras/, raw/, projects/
```

the type of entity (`person`, `company`, …)

```
CoreFrontmatter
```

vault root (`<your-name>.md`, `memexlab.md`)

```
persona | homepage | manifest
```

## AtomicFrontmatter (wiki + engine outputs)

```
<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>date: 2026-04-19                    # required; date of creation (or regeneration for outputs)type: article                       # required; one of the Atomic typestitle: "Deferred net settlement"    # optional; derived from filename if absentstatus: seed                        # required; seed | draft | evergreentags: [topic/settlement, topic/stablecoin]latticework: [problem-1, problem-2] # zero or more of problem-1..problem-5source: 2026-03-17-bloomberg-stablecoin-settlement-rails.md  # optional; present if compiled<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>
```

Required fields. `date`, `type`, `status`, `tags` (can be empty list), `latticework` (can be empty list). Optional fields. `title`, `source`. No extra fields. The schema rejects unknown keys. If you need a new field, edit the schema — don’t smuggle in an ad-hoc key.

## CuratedFrontmatter (ontology + raw + projects)

```
<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>title: "<your-company>"                    # requiredtype: company                       # required; must match the foldercreated: 2025-10-01                 # requiredupdated: 2026-04-19                 # requiredstatus: active                      # required; seed | draft | active | evergreentags: [sector/fintech, hq/istanbul]latticework: [problem-3]# plus type-specific fields (authors for papers, participants for transcripts, etc.)<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>
```

## CoreFrontmatter (root whitelist only)

```
<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>title: "<your-name>"type: personacreated: 2025-09-01updated: 2026-04-19status: activetags: []latticework: []<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>
```

Changes to a core note should be rare; every change is a signal that the system’s anchoring context has shifted.

## Field reference

### date (Atomic only)

ISO `YYYY-MM-DD`. The date the note was created. For engine-generated outputs, the date of generation. This is the field BM25 retrieval uses for timeline bucketing (`memex chart timeline`).

### created / updated (Curated + Core)

Two dates. `created` is set once at birth and never changes. `updated` is updated on every meaningful edit.

### type

The strictest field. Valid values are folder-dependent. The linter will fail a run if a note’s `type` doesn’t match its folder’s allowed set. Adding a new type requires editing `schemas.py` and running `memex migrate`.

### title

Human-readable name. For atomic notes, optional — the filename stem is used when absent. For curated and core notes, required.

Use Title Case for display. Use casefold-aware comparison if you ever hand-search over titles (Turkish `İstanbul` vs `istanbul` is non-trivial).

### status

The maturity of the note.

Status

Meaning

```
seed
```

Just created. Body exists, links may not. Not yet re-read.

```
draft
```

Re-read at least once, cleaned up, links verified.

```
evergreen
```

Revisited weeks or months later, claims re-validated, expected to stand for years.

```
active
```

Curated/core only — the entity is active (the person is alive and relevant, the company exists, the project is underway).

Promotion is manual. Never auto-promote. The whole point of `status` is that a human has signed off.

### tags

See “Tag taxonomy” below.

### latticework

A list of zero or more of `problem-1`, `problem-2`, `problem-3`, `problem-4`, `problem-5`. These are the five Latticework problems:

- Seeing reality clearly

- Deciding under uncertainty

- Allocating time and energy

- Avoiding self-deception

- Playing long games

A note that doesn’t map to any of them is still valid (empty list), but the fact is a soft signal that the note may not deserve canonical space.

### source

Atomic-only. The filename (not full path) of the raw source that produced this note via compile. Used by the linter to verify the citation chain, and by humans to trace claims back to primary text.

## Tag taxonomy

Tags are second-class to `[[wiki-links]]`. Use tags for cross-cutting dimensions that don’t have their own ontology entry. Never use a tag where a link to a canonical note would work.

Tags use slash-namespaced prefixes to keep the namespace organised.

Prefix

Meaning

Examples

```
topic/
```

Thematic — large recurring domains

```
topic/stablecoin, topic/programmable-money, topic/embedded-finance, topic/islamic-finance
sector/
```

Industry / market vertical

```
sector/fintech, sector/banking, sector/regtech
geo/
```

Geographic scope

```
geo/turkey, geo/gcc, geo/eu, geo/us
role/
```

Applied to people

```
role/founder, role/regulator, role/researcher
company/
```

Applied where a note is about a specific company (in addition to the entity link)

```
company/<your-company>, company/<your-product>
audience/
```

On outputs — who the output is for

```
audience/board, audience/public, audience/internal
open-question
```

Flat tag — marks a note as an open research question

```
open-question
reaction/
```

Capture-layer tags for your own in-the-moment reactions

```
reaction/surprising, reaction/skeptical
reading-order/
```

Part of a curated reading path

```
reading-order/stablecoin-101
```

Do this. Keep the prefix set small. New prefixes are a governance decision, not a per-note decision.

Do not do this. Do not create overlapping tag systems. `#stablecoin`, `#Stablecoin`, `#stablecoins`, `#topic/stablecoin` are four different tags in Obsidian — pick one convention (slash-namespaced, lowercase, singular) and stick to it.

## Linking rules

Links (`[[slug]]`) are how the knowledge graph is built. Tags are how it’s sliced.

### When to link

- Every mention of a canonical concept. If a note uses the phrase “deferred net settlement” and the concept has its own atomic note, link it.

- Every reference to an ontology entity. Mentioning <your-company>, Circle, Garry Tan, or Islamic Finance in a note means linking to the entity note.

- Every citation to a raw source. An atomic note should link back to the raw source that supports a claim.

### When not to link

- Inside the archive. No links point into `archive/` from active notes.

- To temporary content. No links to inbox notes.

- To undecided things. If you aren’t sure whether a concept deserves its own note, don’t create a wikilink to a placeholder. Write prose, and revisit when you’ve decided.

### Link format

- By slug, in lowercase. `[[deferred-net-settlement]]`, not `[[Deferred Net Settlement]]`. Obsidian accepts both, but slug form is stable across title renames.

- Block / heading links are allowed but used sparingly. `[[deferred-net-settlement#regulatory-implications]]` is valid; use only when the whole note is too broad a reference.

- Aliases are valid for display. `[[deferred-net-settlement|DNS]]` renders as “DNS” but links correctly. Use for prose flow; do not overuse.

### Broken links

Broken links are errors, not warnings. The linter (`memex lint`) fails the run on any broken wiki-link. If a link points to a note that doesn’t yet exist, either (a) create the note as a stub, or (b) remove the link and write prose instead.

## Entities: linking vs tagging

A common confusion. Both mention <your-company>:

Right. `[[<your-company>]] is piloting embedded finance APIs in Turkey.` — explicit link to the entity note in `companies/`.

Also right, when combined. `[[<your-company>]] is piloting embedded finance APIs in Turkey. #company/<your-company>` — the link carries the graph edge; the tag makes the note discoverable via the `company/` tag facet in Obsidian.

Wrong. `<your-company> is piloting embedded finance APIs in Turkey. #<your-company>` — plain word + flat tag, no link. The graph sees nothing.

Rule of thumb. Links express this note references that entity. Tags express this note is about a theme. Use both when both apply; use links first when in doubt.

## Frontmatter hygiene

Do this. - Let templates generate frontmatter. - Validate with `memex lint` before calling a day done. - Keep the `updated` field on curated notes honest — touching it signals “I looked at this today and it’s still right.”

Do not do this. - Do not copy-paste frontmatter between notes. Schema drift happens this way. - Do not leave empty string values where `None` or missing would be right. An empty `title: ""` is different from `title` being absent. - Do not add arbitrary keys “just to note something”. Use the body or a tag.

## Schema changes

Adding a field, adding a type, or changing a validator is a schema change. The process:

- Edit `memex/schemas.py`.

- Write a migration rule in `memex/modes/migrate.py` that brings existing notes forward. (For additive changes — a new optional field — no migration is required.)

- Run `memex migrate` (dry-run) to preview.

- Run `memex migrate --apply` to execute. Every changed file is snapshotted to `.memex/snapshots/<id>/` first.

- Update these docs.

Schema changes are rare by design. The schemas in the current system took a month of iteration to stabilise; expect any change to have cascading consequences.

---

[← Templates and Note Types](06-templates-and-note-types.md) · [Docs index](README.md) · [Automation and Scripts →](08-automation-and-scripts.md)
