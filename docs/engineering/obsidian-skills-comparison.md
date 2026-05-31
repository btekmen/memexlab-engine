# Comparison: Obsidian Skills vs Agentic Memex

## Short answer

`kepano/obsidian-skills` is a high-quality tool-use layer for Obsidian syntax and operations. Agentic Memex should be a higher-level intelligence architecture: entity schema, provenance, retrieval, benchmarks, and operating workflows.

## Positioning

| Dimension | Obsidian Skills | Agentic Memex |
|---|---|---|
| Primary job | Help agents create/edit Obsidian files correctly | Help agents reason over a citeable knowledge graph |
| Scope | Markdown, Bases, Canvas, Obsidian CLI, web extraction | Entity model, ingestion, curation, retrieval, briefing, evals |
| Unit of work | File syntax and vault operations | Claims, entities, relationships, decisions, sources |
| Data model | Obsidian flavored markdown conventions | Typed entities with provenance and lifecycle |
| Benchmarking | Not central | Core requirement |
| Privacy posture | General-purpose vault tooling | Explicit sanitized/public framework, private data excluded |
| Best use | Editor ergonomics | Strategic/analytical memory system |

## What to borrow

- Agent Skills compatibility.
- Small, focused `SKILL.md` files.
- Clear command recipes.
- Obsidian-native markdown discipline.
- Separate skills for different operations.

## What to avoid

- Staying at the syntax-helper layer.
- Treating the vault as just notes, not as a knowledge substrate.
- Shipping without evals.
- Shipping examples that leak private relationships or real strategy.

## Recommended architecture

Agentic Memex should sit one level above Obsidian Skills:

```text
Obsidian / Markdown editor layer
        ↑
Obsidian Skills: syntax, bases, canvas, CLI
        ↑
Agentic Memex: entity schema, provenance, graph, retrieval, evals, briefings
        ↑
User-facing agent: answers, decisions, prep, memory maintenance
```

## Interoperate (use them together)

MemexLab and [`kepano/obsidian-skills`](https://github.com/kepano/obsidian-skills) (MIT, by
Steph Ango / kepano) both follow the **Agent Skills specification**, so they install side by
side in the same agent and compose cleanly — obsidian-skills handle the **vault / file layer**,
MemexLab handles the **knowledge layer**.

Install both (works for OpenClaw / Claude Code / Codex / OpenCode agents):

```bash
npx skills add kepano/obsidian-skills    # obsidian-markdown, obsidian-bases, json-canvas, obsidian-cli, defuddle
# then add MemexLab's skills/ to the same agent skills directory
```

How they compose:

| kepano/obsidian-skills | …feeds / supports | MemexLab |
| --- | --- | --- |
| `defuddle` (clean HTML → markdown) | source capture | `memex-ingest` / `memex-extract` |
| `obsidian-markdown` | correct file syntax for the items MemexLab writes | `memex-markdown` |
| `obsidian-bases` | tabular views over MemexLab's typed frontmatter | schema / `memex-progress` coverage |
| `json-canvas` | visual maps of the knowledge graph | concept maps / relationships |
| `obsidian-cli` | vault file operations | all write paths |

Use obsidian-skills for *operating Obsidian correctly*; use MemexLab for *operating the
knowledge*. We link to obsidian-skills rather than bundling it — see its
[repo](https://github.com/kepano/obsidian-skills) for current skills and install.

## Benchmark axes

1. Retrieval precision: did the system find the right entities and sources?
2. Citation quality: are claims tied to actual source notes?
3. Synthesis quality: does the answer sharpen the user’s decision?
4. Deduplication: does it merge duplicate people/companies/sources safely?
5. Contradiction handling: does it flag conflicts instead of smoothing them over?
6. Privacy safety: does it avoid leaking private material into public outputs?
