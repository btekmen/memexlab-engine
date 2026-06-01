---
type: index
title: "Worked example — extract, frameworks, progress"
status: active
tags: [example, walkthrough]
---

# Worked example — extract → frameworks → progress

A complete, runnable-on-paper pass of the MemexLab pipeline over one real, public source:
Vannevar Bush's **"As We May Think"** (The Atlantic, 1945) — fittingly, the essay that named
the *memex*. It shows the three capabilities end to end, with real artifacts you can read.

> No source text is reproduced — only paraphrased claims with provenance, exactly as the
> system is designed to work.

## The pass

| Step | Skill | Input → Output | Artifact |
| --- | --- | --- | --- |
| 1. Ingest | `memex-ingest` | the essay → a source note with provenance | [`sources/as-we-may-think.md`](sources/as-we-may-think.md) |
| 2. Extract | `memex-extract` | source → atomic, cited concept items | [`items/`](items/) (4 concepts) |
| 3. Frameworks | `memex-frameworks` | items → a lensed synthesis (first-principles · second-order · inversion) | [`synthesis/trails-to-agent-memory.md`](synthesis/trails-to-agent-memory.md) |
| 4. Progress | `memex-progress` | vault → coverage, gaps, learn-next | [`synthesis/progress-note.md`](synthesis/progress-note.md) |

## What to notice

- **Provenance everywhere** — every concept carries `source: sources/as-we-may-think.md` and a `[[wikilink]]` back to it.
- **Frameworks turn facts into judgment** — the same four extracted facts, run through three lenses, yield *why Bush's idea matters for agent memory today* (and the risks it implies).
- **Progress is computed, not asserted** — the coverage map flags that `problem-2` and `problem-4` are unserved, and names the next thing to read.
- **It validates** — `python3 scripts/validate_vault.py examples/worked-example` passes.

## Run the check

```bash
python3 scripts/validate_vault.py examples/worked-example
```
