---
name: memex-progress
description: Track and advance learning over time — coverage across the latticework problems, gap detection, spaced revisiting, and eval-driven quality.
---

# Memex Progress

## Workflow

1. Build a coverage map: evergreen items per latticework problem and per domain.
2. Detect gaps: flag under-served problems/domains, plus orphan and stub items.
3. Schedule spaced revisiting: surface evergreen items due for review (recency × importance) to strengthen or retire.
4. Track mastery signals: citations-in, links-in, eval scores, and contradiction flags per topic.
5. Suggest learn-next: the highest-leverage gaps and the sources that would close them.
6. Record progress: write a dated synthesis item and compare eval scores over time.

## Output discipline

- Coverage and gaps are computed from the vault, not guessed.
- Spaced revisiting prompts review; it never edits notes unattended.
- Progress is measured (eval scores, coverage deltas), not asserted.
