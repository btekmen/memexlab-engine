# Templates and Note Types

Templates live at `templates/` in the vault and are invoked via Obsidian’s Templater plugin. Every template produces a note with valid frontmatter, correct folder placement, and a minimal skeleton body. You should never hand-construct a note’s frontmatter — let the template do it.

All templates below assume the `Templater` plugin is installed and the user configures it to look at `templates/`. A recommended setup is in `09-onboarding.md`.

## Template inventory

Template

Produces a note in

Frontmatter

When to use

```
source.md
raw/
CuratedFrontmatter
```

Web articles, short-form sources

```
paper.md
raw/
CuratedFrontmatter
```

Academic / working papers

```
transcript.md
raw/
CuratedFrontmatter
```

Meeting recordings, interviews

```
memo.md
```

`raw/` or `projects/`

varies

Internal written sources (yours or shared)

```
concept.md
wiki/
AtomicFrontmatter
```

A new canonical concept page

```
person.md
people/
CuratedFrontmatter
```

A new person entity

```
company.md
companies/
CuratedFrontmatter
```

A new company entity

```
philosophy.md
philosophies/
CuratedFrontmatter
```

A new stance / worldview

```
era.md
eras/
CuratedFrontmatter
```

A new temporal frame

```
project.md
projects/<slug>/
CuratedFrontmatter
```

A new active project

```
slides.md
```

`projects/.../` or handwritten decks

AtomicFrontmatter + Marp

A hand-authored deck (engine-written decks use the `export slides` command)

```
daily-note.md
```

`daily/YYYY-MM-DD.md` (optional folder)

minimal

A dated journal / planner

## source.md — web articles, short-form

Purpose. The standard raw-source note for material pulled from the web: news, blog posts, podcasts, tweets (as threaded excerpts).

Filename. `YYYY-MM-DD-publisher-short-title.md` in `raw/`.

Frontmatter.

```yaml
---
title: "Stablecoin settlement rails face a netting crisis"
type: source
source_url: https://www.bloomberg.com/…
publisher: Bloomberg
author: Jane Doe
publication_date: 2026-03-17
ingested: 2026-03-18
status: seed
tags: [topic/stablecoin, topic/settlement]
latticework: [problem-1, problem-2]
---
```

Body skeleton.

```markdown
## Original text
<full verbatim article text here>
## Reactions
- <your reaction, time-stamped if useful>
## Related
- [[deferred-net-settlement]]
```

When to use. Any web source you want to cite later. If you never plan to cite it, skip — leave it in the inbox until you’re sure.

## paper.md — academic / working papers

Purpose. Longer, structured sources: BIS working papers, IMF research, regulatory filings, academic journals.

Filename. `YYYY-MM-DD-venue-<slug>.md` in `raw/`. Date is the ingestion date.

Frontmatter.

```yaml
---
title: "Interoperability of wholesale central bank digital currencies"
type: paper
authors: [Auer, Boehme, Clark]
venue: "BIS Working Paper No 1112"
publication_date: 2025-10-12
doi: "10.…"
pages: 48
ingested: 2025-11-04
status: seed
tags: [topic/cbdc, topic/interop]
latticework: [problem-1]
---
```

Body skeleton.

```markdown
## Abstract
<copy from the paper>
## Full text
<extracted text here — pdf-to-text output is fine>
## My notes
- <terse margin notes>
## Related
- [[wholesale-cbdc-definition]]
```

When to use. Any longer-form published research. Compile these after reading, not before.

## transcript.md — interviews, meetings, voice memos

Purpose. Captured speech. The goal is the raw text — interpretation happens downstream.

Filename. `YYYY-MM-DD-<kind>-<short-desc>.md` in `raw/`.

Frontmatter.

```yaml
---
title: "Central bank operator interview — T+0 feasibility"
type: transcript
participants: [<your-name>, Jane Operator]
recorded: 2026-02-20
duration_minutes: 52
source: zoom
ingested: 2026-02-21
status: seed
tags: [topic/settlement, topic/regulation]
latticework: [problem-1]
---
```

Body skeleton.

```markdown
## Context
<one paragraph on why this meeting happened>
## Transcript
<verbatim transcript — Whisper output, manually reviewed for name spelling>
## Action items
- <if any>
## Related
- [[t-plus-zero-settlement]]
```

When to use. Any non-trivial spoken source. One-off 15-minute calls are usually better captured as inbox notes and never promoted.

## memo.md — internal written sources

Purpose. Internal documents you author or receive. <your-company> strategy memos, <your-product> investor updates, personal long-form writing you want to treat as raw material for later atomization.

Filename. `YYYY-MM-DD-<org>-<short-title>.md`.

Frontmatter.

```yaml
---
title: "Q1 2026 platform strategy refresh"
type: memo
author: <your-name>
org: <your-company>
date_written: 2026-01-15
ingested: 2026-01-20
status: draft
tags: [company/<your-company>, topic/strategy]
latticework: [problem-3, problem-5]
---
```

When to use. Any document written for a specific organisational context that you later want to treat as a source for atomic extraction.

## concept.md — new canonical concept page

Purpose. The most-used template. Produces a fresh atomic note in `wiki/`.

Filename. `<slug>.md` in `wiki/`.

Frontmatter.

```yaml
---
date: 2026-04-19
type: article
title: "Deferred net settlement"
status: seed
tags: [topic/settlement, topic/stablecoin]
latticework: [problem-1]
source: 2026-03-17-bloomberg-stablecoin-settlement-rails.md  # if compiled
---
```

Body skeleton.

```markdown
# Deferred net settlement
<1–2 sentence definition>
## What it is
<3–5 sentences>
## Why it matters
<3–5 sentences tying it back to at least one of the Latticework problems>
## Related
- [[gross-settlement]]
- [[netting-risk]]
- [[pre-funded-stablecoin-float]]
```

When to use. Whenever you create a new wiki note by hand (i.e., not through `memex compile`). The compiler uses its own internal template; you don’t need to invoke this one after compile.

## person.md, company.md, philosophy.md, era.md — ontology entries

Four templates, same shape. The `type` field varies.

Filename. `<slug>.md` in the matching folder.

Frontmatter (person example).

```yaml
---
title: "Garry Tan"
type: person
created: 2026-01-10
updated: 2026-04-19
status: active
tags: [role/investor, domain/startups]
latticework: [problem-1]
affiliations: [y-combinator]
---
```

Body skeleton.

```markdown
# Garry Tan
<one-paragraph biography>
## Relevant work
- <bullet with `[[link]]` to the atomic notes that discuss this person's claims, papers, or decisions>
## Key positions
- <positions you've tracked>
## Sources
- [[2021-founder-essay]]
```

When to use. The first time you want to cite an entity and you expect to cite it again. A one-off mention does not deserve its own entity note.

Do this. Create the entity note lazily but decisively — wait until a concept note wants to link to it, then create the entity and the link together.

Do not do this. Do not pre-populate dozens of entity notes “just in case”. Empty entity notes are lint noise.

## project.md — new active project

Purpose. Produces the project folder skeleton.

Location. Creates `projects/<slug>/` with `index.md`, empty `notes/`, empty `outputs/`.

Frontmatter of `index.md`.

```yaml
---
title: "Stablecoin settlement whitepaper — 2026 Q2"
type: project
created: 2026-04-01
updated: 2026-04-19
status: active
target_end_date: 2026-06-30
tags: [topic/stablecoin, topic/settlement]
latticework: [problem-2, problem-5]
---
```

Body skeleton (`index.md`).

```markdown
# Stablecoin settlement whitepaper — 2026 Q2
**Goal.** A 20-page whitepaper articulating a position on deferred-net-settlement vs gross-settlement tradeoffs for stablecoin infrastructure, with a regulatory-compatibility appendix.
**Deadline.** 2026-06-30.
**Deliverables.**
- Whitepaper draft (20pp)
- Slide deck for board presentation (15 slides)
- One-page executive summary
## Canonical notes I'll pull from
- [[deferred-net-settlement]]
- [[gross-settlement]]
- [[mica-settlement-implications]]
## Open questions
- [[does-the-gcc-adopt-wholesale-cbdc-before-2028]]
## Work log
- 2026-04-01 — project created
```

When to use. Any goal-driven work with a specific deliverable and end date. Not for always-on themes (those are `wiki/`).

## slides.md — hand-authored decks

Most decks are generated by `memex export slides`. This template is for the rare case you want to author one by hand.

Filename. `projects/<project>/outputs/<slug>.md`, or standalone `_slides/slides-<slug>.md` if you want to hand-write one into the engine’s deck folder.

Frontmatter (Marp-compatible).

```yaml
---
marp: true
theme: gaia
date: 2026-04-19
type: slides
title: "Programmable Money Primer — <your-product> Board"
status: draft
tags: [topic/programmable-money, audience/board]
latticework: [problem-2, problem-5]
---
```

Body skeleton.

```markdown
# Programmable Money Primer
<your-product> Board — 2026-04-19 ## Why this matters now
- <bullet>
- <bullet> ## The three architectures
<slide body>
```

When to use. Rarely. Prefer `memex export slides "<topic>" --theme gaia --apply` and edit the output. Hand-authored decks bypass the retrieval layer, which means they can silently drift from the vault.

## daily-note.md — journal / planner

Purpose. An optional daily-note file for short, dated entries: what you worked on, what you noticed, what questions arose.

Filename. `daily/YYYY-MM-DD.md` (folder is optional — many operators skip daily notes entirely).

Frontmatter.

```yaml
---
date: 2026-04-19
type: daily
---
```

Body skeleton.

```markdown
# 2026-04-19
## What I did
- <entries>
## What I noticed
- <entries>
## Questions that came up
- <entries, candidates for `wiki/questions/`>
```

When to use. If daily notes help you trace decisions weeks later, use them. If they become a chore, skip them — the inbox + weekly review handles the same work differently.

## Template principles

- Templates produce valid frontmatter. The schema is never optional. If a template can’t produce valid frontmatter for the data at hand, fix the template.

- Templates are minimal. A skeleton body is a set of section headers and `<placeholders>`. Do not pre-fill content — you’re not writing for an AI, you’re writing for yourself.

- One template per note type. Do not create variant templates (“a paper template with no DOI”, “a person template for contacts only”). If the variant matters, it becomes a new `type` in the schema.

- Templates version with the vault. The `templates/` folder is part of the vault; changes to templates flow to future notes but not past ones. A schema change (`memex migrate`) is how you retroactively apply a structural change.

---

[← Daily Workflow](05-daily-workflow.md) · [Docs index](README.md) · [Metadata and Tagging Rules →](07-metadata-and-tagging-rules.md)
