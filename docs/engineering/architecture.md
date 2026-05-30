
# Memex Architecture

Memex is a local-first, markdown-native second-brain framework optimized for strategic synthesis, not passive note collection. The markdown vault is the source of truth; schemas, indexes, skills, and evals are operating layers around it.

## Lineage

Primary credit goes to Andrej Karpathy's LLM Knowledge Bases / LLM Wiki pattern: raw sources stay intact, an LLM maintains a persistent markdown wiki, and answers can be filed back into the wiki so knowledge compounds. Memex extends that idea with schemas, skills, validation, governance, evals, and a clean public/private vault boundary.

Garry Tan's GStack and GBrain are major operational influences: GStack for skill-based agent workflows, and GBrain for retrieval, graph traversal, cited synthesis, and local-first brain operations.

See [Lineage and Credits](lineage.md).

## Design goals

1. **Durability** — notes should remain useful years later.
2. **Traceability** — synthesized claims should point back to sources.
3. **Composability** — individual notes should become inputs for maps, essays, decisions, and strategy.
4. **Searchability** — metadata should support both human browsing and future machine retrieval.
5. **Agent-operability** — workflows should be repeatable by an AI agent with citations and guardrails.
6. **Low ceremony** — structured enough to compound, simple enough to use daily.

## System layers

1. **Raw/source layer** — original or lightly cleaned inputs: articles, exports, transcripts, PDFs, bookmarks, conversations, research snippets.
2. **Compiled wiki/content layer** — human-readable markdown entities, synthesized items, maps, and decision notes.
3. **Schema and index layer** — JSON schemas, front matter conventions, content indexes, graph edges, and provenance.
4. **Machine layer** — lexical indexes, embeddings, metadata tables, and eval traces.
5. **Agent workflow layer** — repeatable skills for ingest, query, curation, briefing, markdown editing, and evaluation.
6. **Interface layer** — chat, CLI, editor, GitHub Pages, and scheduled maintenance.
7. **Harness layer** — execution boundaries, tool contracts, context policy, lifecycle state, observability, verification, and governance.

See [Harness Architecture](harness-architecture.md) for the ETCLOVG mapping.

## Memory horizons

| Horizon | Memex layer | Purpose | Example artifacts |
| --- | --- | --- | --- |
| Active context | Current agent/session window | Immediate reasoning state | Current prompt, retrieved files, tool results |
| Mid-term state | Session and task handoff files | Recover work across turns, compactions, and restarts | Daily memory files, task notes, state templates |
| Long-term memory | Brain/Memex markdown plus indexes | Durable recall and synthesis across projects | Entity pages, source notes, items, GBrain index |

Long-running work should not trust chat history as the source of truth. Important state must move into durable files with provenance, uncertainty markers, and last-verified timestamps.

## Information model

### 1. Sources

Path: `content/sources/`

Sources are evidence and raw material. They are not expected to be polished.

Examples:

- book notes
- article excerpts
- transcripts
- meeting notes
- research snippets
- copied source markdown

### 2. Items

Path: `content/items/`

Items are synthesized notes. Each item should include:

- title
- type
- ingestion or creation date
- source references
- tags
- core thesis
- key ideas
- reusable frameworks or questions

Items should be opinionated. A good item says what matters and why.

### 3. Index

Path: `content/index.jsonl`

The index provides machine-readable metadata for each item. One JSON object per line.

Required fields:

- `id`
- `title`
- `path`
- `source_files`
- `tags`
- `ingested_at`

### 4. Entity pages

Future or expanded vaults can use typed entity pages for:

- `person`
- `company`
- `concept`
- `project`
- `source`
- `decision`
- `relationship`
- `synthesis`
- `index`

Entity pages make the memex graph-readable and allow agents to resolve people, companies, concepts, and relationships directly.

### 5. Maps

Future path: `content/maps/`

Maps connect multiple items into larger structures:

- mental models
- strategic themes
- decision frameworks
- company or market theses
- reading programs

Examples:

- AI deterrence and sovereign capability
- Digital banking infrastructure in emerging markets
- Long games and compounding institutions
- Clear thinking under uncertainty

## Naming conventions

Use stable, human-readable slugs:

```text
YYYY-MM-DD-short-topic-slug.md
```

Example:

```text
2026-05-09-technological-republic-ai-deterrence.md
```

## Metadata conventions

Items use YAML front matter. Keep field names consistent so future tooling can parse them.

```yaml
---
title: "Example Title"
type: memex_ingest
ingested_at: "2026-05-14T07:50:00+03:00"
source_files:
  - "content/sources/example.md"
tags:
  - "AI"
  - "strategy"
---
```

## Claim discipline

Every analytical answer should separate:

- **Cited fact** — grounded in a note or source path.
- **Inference** — the agent's judgment based on cited facts.
- **Unknown** — missing or insufficient evidence.

## Public and private boundary

This repository contains the framework: documentation, templates, schemas, skills, eval methodology, synthetic example vaults, and public-source examples.

Real deployments should keep private vault data in a separate, access-controlled repository. Private vaults can reuse the same schema and skills without exposing real people, meetings, investor materials, customer records, or strategy.

## Search and retrieval modes

Use the smallest retrieval mode that can answer the question:

1. Exact lookup: known slug or known file path.
2. Keyword search: names, companies, exact phrases, source titles.
3. Hybrid query: concepts, analogies, strategic themes, fuzzy recall.
4. Graph traversal: neighboring people, companies, relationships, decisions.
5. Eval set: regression checks for expected entities, citation quality, and synthesis quality.

## Agent operating rule

Agents should not treat the vault as generic prompt context. They should resolve entities, retrieve sources, separate cited facts from inference, write durable updates only with provenance, run validation after structural edits, and avoid publishing private vault material.

## Future automation

The current repository is intentionally simple. Later automation can add:

- index rebuilding
- duplicate detection
- semantic search
- graph extraction
- tag normalization
- source-to-item traceability checks
- privacy scans
- benchmark reports
- weekly synthesis reports
