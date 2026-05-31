---
name: memex-extract
description: Extract durable knowledge from long-form sources (books, reports, papers) into atomic, cited memex items without losing provenance.
---

# Memex Extract

## Workflow

1. Register the source with `memex-ingest` (immutable, with provenance).
2. Chunk the source into passages (by chapter/section; keep page or location refs).
3. From each chunk, extract candidates: claims, key concepts, notable quotes, decisions, open questions.
4. Attach provenance to every candidate: source slug + page/location.
5. Dedupe against existing items (BM25 + embeddings); merge into the strongest note rather than duplicating.
6. Propose atomic items via `memex-markdown` for net-new claims/concepts; link each quote to its concept.
7. Refresh the indexes (BM25 + embeddings) so new items are immediately queryable.

## Output discipline

- Every extracted claim carries a source path and page/location.
- A quote is verbatim and attributed — never paraphrase into a quote.
- Prefer merging into an existing item over creating a near-duplicate.
- Mark inference vs. source-stated fact explicitly.
- Writes are dry-run; a human approves before apply.
