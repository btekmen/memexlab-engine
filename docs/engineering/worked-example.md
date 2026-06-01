# Worked example: As We May Think

A complete, **validating** pass of the MemexLab pipeline over one real public source — Vannevar
Bush's *As We May Think* (The Atlantic, 1945), the essay that named the *memex*. It shows the
three capabilities end to end with real, cited artifacts.

> No source text is reproduced — only paraphrased claims with provenance, exactly as the system
> is designed to work. The full vault lives in the repo and passes `validate_vault.py`.

## The pass

| Step | Skill | Output | Artifact |
| --- | --- | --- | --- |
| 1. Ingest | `memex-ingest` | a source note with provenance | [`sources/as-we-may-think.md`](https://github.com/btekmen/memexlab-engine/blob/main/examples/worked-example/sources/as-we-may-think.md) |
| 2. Extract | `memex-extract` | four atomic, cited concept items | [`items/`](https://github.com/btekmen/memexlab-engine/tree/main/examples/worked-example/items) |
| 3. Frameworks | `memex-frameworks` | a lensed synthesis (first-principles · second-order · inversion) | [`trails-to-agent-memory.md`](https://github.com/btekmen/memexlab-engine/blob/main/examples/worked-example/synthesis/trails-to-agent-memory.md) |
| 4. Progress | `memex-progress` | coverage, gaps, learn-next | [`progress-note.md`](https://github.com/btekmen/memexlab-engine/blob/main/examples/worked-example/synthesis/progress-note.md) |

## What to notice

- **Provenance everywhere** — every concept carries `source: sources/as-we-may-think.md` and a `[[wikilink]]` back to it.
- **Frameworks turn facts into judgment** — the four extracted facts, run through three lenses, yield *why Bush's idea matters for agent memory today* and the risks it implies.
- **Progress is computed, not asserted** — the coverage map flags `problem-2` and `problem-4` as unserved and names the next read.
- **It validates** — `python3 scripts/validate_vault.py examples/worked-example` passes.

Browse the full example in the repo: [`examples/worked-example/`](https://github.com/btekmen/memexlab-engine/tree/main/examples/worked-example).

---

[← Learning & Frameworks](learning-and-frameworks.md) · [Engineering & design](README.md)
