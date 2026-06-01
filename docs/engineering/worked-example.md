# Worked example: four sources, one pipeline

A complete, **validating** run of the MemexLab pipeline over **four real, public sources** —
showing the three capabilities end to end with cited artifacts, and the learning loop closing
its own coverage gaps.

> No source text is reproduced — only paraphrased claims with provenance. The full vault passes
> `validate_vault.py`. Browse it:
> [`examples/worked-example/`](https://github.com/btekmen/memexlab-engine/tree/main/examples/worked-example).

## Sources

| Source | Author | Year |
| --- | --- | --- |
| *As We May Think* (the essay that named the *memex*) | Vannevar Bush | 1945 |
| *Skunk Works* | Ben R. Rich, Leo Janos | 1994 |
| *Grace Hopper and the Invention of the Information Age* | Kurt W. Beyer | 2009 |
| *The Art of Doing Science and Engineering* | Richard W. Hamming | 1997 |

## The pass

| Step | Skill | Artifacts |
| --- | --- | --- |
| 1. Ingest | `memex-ingest` | [source notes](https://github.com/btekmen/memexlab-engine/tree/main/examples/worked-example/sources) — one per book, with provenance |
| 2. Extract | `memex-extract` | 11 cited [concept items](https://github.com/btekmen/memexlab-engine/tree/main/examples/worked-example/items) |
| 3. Frameworks | `memex-frameworks` | lensed [syntheses](https://github.com/btekmen/memexlab-engine/tree/main/examples/worked-example/synthesis) (first-principles · second-order · inversion; cross-source) |
| 4. Progress | `memex-progress` | [coverage, gaps, learn-next](https://github.com/btekmen/memexlab-engine/blob/main/examples/worked-example/synthesis/progress-note.md) |

## What to notice

- **Provenance everywhere** — every concept carries a `source:` and a `[[wikilink]]` back to it.
- **Frameworks turn facts into judgment** — extracted facts run through mental-model lenses yield *why these ideas matter for agent memory*.
- **The learning loop closes its own gaps** — pass 1 (Bush only) flagged `problem-2` and `problem-4` as unserved; reading Hamming closes both, and coverage now spans all five latticework problems.
- **Cross-source synthesis** — *the compounding stack* connects Hopper (abstraction) + Bush (maintenance) + Hamming (judgment) + Skunk Works (execution).
- **It validates** — `python3 scripts/validate_vault.py examples/worked-example` passes.

---

[← Learning & Frameworks](learning-and-frameworks.md) · [Engineering & design](README.md)
