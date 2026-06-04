# Library

The [`library/`](https://github.com/btekmen/memexlab-engine/tree/main/library) is a growing
collection of MemexLab **knowledge assets** — synthesized notes distilled from papers, reports,
and books, each with provenance, key ideas, and atomic-note candidates. It is the durable output
the system exists to produce: read something, turn it into a citable asset, let it compound.

It currently holds a paper (*Attention Is All You Need*), a strategic report (Benedict Evans,
*AI eats the world*), and a growing shelf of books spanning AI, technology history, and strategy —
from *Skunk Works* and *Broken Genius* to *Life 3.0*, *The Coming Wave*, and *Empire of AI*. The
current, always-up-to-date list lives in the generated index:
[`library/README.md`](https://github.com/btekmen/memexlab-engine/blob/main/library).

## Add an asset (it slots in cleanly)

1. Drop a markdown file into `library/papers/`, `library/reports/`, or `library/books/` with frontmatter:

   ```yaml
   ---
   type: source
   title: "Title"
   author: "Author"        # or authors: [A, B]
   year: 2024
   url: https://...         # canonical source — we link, never vendor the PDF
   tags: [paper, ...]
   ---
   ```

2. Body: a short summary, the key ideas, and `[[atomic note]]` candidates.
3. Regenerate the index:

   ```bash
   python3 scripts/build_library_index.py
   ```

The index groups assets by type and lists title / author(s) / year — no manual editing.

## Papers vs. the worked example

- The **[worked example](worked-example.md)** demonstrates the *pipeline* (ingest → extract → frameworks → progress) on a fixed set of sources.
- The **library** is the *output* — the durable, growing corpus those passes produce, one asset per source.

Papers and reports link to their canonical source (e.g. arXiv, the author's site) rather than
bundling the PDF: the asset is the *distilled* knowledge, not a copy of the source.

---

[← Engineering & design](README.md) · [Worked example](worked-example.md)
