# Learning & Frameworks

How MemexLab turns long-form inputs into durable understanding that compounds. Three
capabilities work together: **extraction** (get the knowledge in, with provenance),
**frameworks** (interrogate it with mental models), and **progressive learning** (revisit,
measure, and close gaps over time).

```
sources (books, reports, papers)
   │  memex-extract
   ▼
atomic items  ──  memex-frameworks (apply lenses, tag latticework)
   │
   ▼  memex-progress (coverage · gaps · spaced review · eval)
durable, compounding understanding
```

## 1. Extraction from reports & books

The [`memex-extract`](../../skills/memex-extract/SKILL.md) skill turns a long source into
cited atomic items without losing provenance.

- **Chunk** by chapter/section, preserving page or location references.
- **Extract** candidates per chunk: claims, key concepts, notable quotes, decisions, open questions.
- **Provenance by default** — every candidate carries `source:` (slug) and a page/location.
- **Dedupe before write** — match candidates against existing items with BM25 **and**
  embeddings; merge into the strongest note rather than spawning near-duplicates.
- **Quotes are verbatim and attributed**; inference is marked separately from source-stated fact.
- Writes are dry-run; a human approves before apply.

For web sources, [`kepano/obsidian-skills`](https://github.com/kepano/obsidian-skills)'
`defuddle` skill is a recommended companion — it turns a messy page into clean markdown that
`memex-extract` then distills into cited items. See
[Obsidian Skills: comparison & interop](obsidian-skills-comparison.md).

### Retrieval: BM25 + embeddings

Retrieval is hybrid and **provider-agnostic**. Deterministic BM25 gives exact-term recall and
reproducibility; an embedding index (any provider — OpenAI, or a local model) gives semantic
recall for paraphrased or conceptually-related material. Extracted items are indexed into both
on write, so a query like *"netting risk in deferred settlement"* finds the relevant claim even
when the source never used those words. The vault stays the source of truth; the indexes are a
disposable acceleration layer, rebuildable from the markdown at any time.

## 2. Mental frameworks

Capture is cheap; **judgment** is the scarce asset. The
[`memex-frameworks`](../../skills/memex-frameworks/SKILL.md) skill applies named **lenses** from
the [`frameworks/`](../../frameworks/README.md) library — first-principles, inversion,
second-order effects, base rates, incentives — as structured passes over a topic or item.

- A lens produces **assumptions, failure modes, questions, and framings — not invented facts**.
- Items are tagged by the framework used **and** the latticework problem they serve
  (`problem-1` … `problem-5`, the five-problem meta-taxonomy).
- The reasoning is cross-linked to the lens notes, so *why* a conclusion was reached stays
  inspectable.

This is how a raw claim becomes a *thinking asset*: the same fact, run through inversion and
second-order effects, yields the risks and downstream consequences a flat summary misses.

## 3. Progressive learning

The [`memex-progress`](../../skills/memex-progress/SKILL.md) skill makes the vault improve over
time instead of merely accumulating.

- **Coverage map** — evergreen items per latticework problem and per domain; a readable signal
  of what you're thinking about and what you're neglecting.
- **Gap detection** — under-served problems/domains, orphan notes, and stubs surface as the
  next things to learn.
- **Spaced revisiting** — evergreen items become due for review on a recency × importance
  schedule; each pass strengthens, splits, or retires the note. (Review is *surfaced*, never
  applied unattended.)
- **Mastery signals** — citations-in, links-in, eval scores, and contradiction flags per topic.
- **Learn-next** — the highest-leverage gaps, and the sources that would close them.
- **Measured, not asserted** — progress is tracked as eval-score and coverage deltas over time
  (see [Benchmark Report](benchmark-report.md) and [Observability](observability.md)).

## How it compounds

Extraction fills the vault with cited claims; frameworks turn claims into judgment and tag them
to the problems that matter; progressive learning revisits the weak spots and measures whether
quality is actually rising. Each loop deepens the corpus and improves the next answer — the
opposite of re-deriving from scratch every session.

---

[← Engineering & design](README.md) · [Operating System](operating-system.md) · [Taxonomy](taxonomy.md)
