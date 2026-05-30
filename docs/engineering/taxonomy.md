# Memex Taxonomy

This taxonomy keeps the second brain searchable and useful without becoming bureaucratic.

## Note types

Use `type` in YAML front matter.

Recommended values:

- `memex_ingest` — synthesized note created from one or more sources
- `book_note` — structured book synthesis
- `article_note` — article or essay synthesis
- `meeting_note` — private meeting or conversation synthesis
- `mental_model` — reusable thinking model
- `strategy_note` — company, market, or geopolitical strategy note
- `question` — durable strategic or philosophical question
- `map` — synthesis across multiple notes

## Tag rules

Tags should be useful for retrieval, not exhaustive.

Good tags usually represent:

- person: `Alex Karp`, `Charlie Munger`
- organization: `Palantir`, `<your-company>`
- domain: `AI`, `digital banking`, `national security`
- concept: `deterrence`, `compounding`, `inversion`
- geography: `Turkey`, `Pakistan`, `Indonesia`
- project: `The Latticework Project`, `Clear Thinker's Path`

Avoid tags that are too generic:

- `interesting`
- `notes`
- `important`
- `misc`

## Suggested strategic domains

- AI and sovereign capability
- Digital banking infrastructure
- Emerging markets
- Regulation and institutional design
- Capital markets and IPO readiness
- Leadership and talent density
- Mental models and clear thinking
- Long games and compounding
- Geopolitics and hard power

## Front matter standard

```yaml
---
title: ""
type: memex_ingest
ingested_at: "YYYY-MM-DDTHH:MM:SS+03:00"
source_files: []
tags: []
---
```

Optional fields:

```yaml
author: ""
source_url: ""
created_at: ""
updated_at: ""
status: draft|active|archived
confidence: low|medium|high
related: []
```

## Review rules

During review, ask:

1. Is this tag still useful?
2. Are two tags synonyms that should merge?
3. Does this item belong in a larger map?
4. Has this idea affected a real decision?
5. Should this be archived?
