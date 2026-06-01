---
type: index
title: "Worked example — extract, frameworks, progress"
status: active
tags: [example, walkthrough]
---

# Worked example — extract → frameworks → progress

A complete, **validating** run of the MemexLab pipeline over **four real, public sources**, showing
the three capabilities end to end with cited artifacts — and the *learning loop* closing its own gaps.

> No source text is reproduced — only paraphrased claims with provenance, exactly as the system
> is designed to work. The full vault passes `validate_vault.py`.

## Sources

| Source | Author | Year |
| --- | --- | --- |
| [As We May Think](sources/as-we-may-think.md) (the essay that named the *memex*) | Vannevar Bush | 1945 |
| [Skunk Works](sources/skunk-works.md) | Ben R. Rich, Leo Janos | 1994 |
| [Grace Hopper and the Invention of the Information Age](sources/grace-hopper.md) | Kurt W. Beyer | 2009 |
| [The Art of Doing Science and Engineering](sources/the-art-of-doing-science-and-engineering.md) | Richard W. Hamming | 1997 |

## The pass

| Step | Skill | Output |
| --- | --- | --- |
| 1. Ingest | `memex-ingest` | a [source note](sources/) per book, with provenance |
| 2. Extract | `memex-extract` | 11 atomic, cited [concept items](items/) |
| 3. Frameworks | `memex-frameworks` | lensed syntheses — [trails → agent memory](synthesis/trails-to-agent-memory.md) and the cross-source [compounding stack](synthesis/the-compounding-stack.md) |
| 4. Progress | `memex-progress` | [coverage, gaps, learn-next](synthesis/progress-note.md) |

## What to notice

- **Provenance everywhere** — every concept carries a `source:` and a `[[wikilink]]` back.
- **Frameworks turn facts into judgment** — extracted facts, run through mental-model lenses, yield *why these ideas matter for agent memory* (first-principles, second-order, inversion).
- **The learning loop closes gaps** — pass 1 (Bush only) flagged `problem-2` and `problem-4` as unserved; reading Hamming in pass 2 closes both. Coverage now spans all five latticework problems.
- **Cross-source synthesis** — `the-compounding-stack` connects Hopper (abstraction) + Bush (maintenance) + Hamming (judgment) + Skunk Works (execution).
- **It validates** — `python3 scripts/validate_vault.py examples/worked-example` passes.

## Run the check

```bash
python3 scripts/validate_vault.py examples/worked-example
```
