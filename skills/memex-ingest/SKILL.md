---
name: memex-ingest
description: Ingest raw sources into a local-first memex without losing provenance or polluting curated entity pages.
---

# Memex Ingest

## Workflow

1. Save original artifact into raw/source storage.
2. Extract readable markdown.
3. Create or update a source note.
4. Identify candidate entities.
5. Propose curation changes; do not overwrite curated pages blindly.
6. Rebuild machine indexes.
