---
type: synthesis
title: From associative trails to agent memory
status: active
tags: [example, synthesis, frameworks]
latticework: [problem-1, problem-5]
source: sources/as-we-may-think.md
---

# From associative trails to agent memory

A `memex-frameworks` pass over [[the-memex]] and [[associative-trails]], read against today's
LLM agents. Lenses applied: **first-principles**, **second-order effects**, **inversion**.

## First principles

Strip Bush's memex to fundamentals: immutable records + user-curated links + a maintained
trail. None of that requires the 1945 mechanics (microfilm) — it requires a durable store and a
**maintainer**. The missing piece in 1945 was the maintainer; an LLM can now supply it.

## Second-order effects

If an agent maintains the trails (not just the human): trails compound without manual upkeep →
retrieval improves as the corpus grows → the marginal cost of a good answer falls over time.
The risk that emerges — the maintainer can also quietly *corrupt* the record — is why
provenance, dry-run, and human approval exist.

## Inversion

How would agent-maintained memory reliably fail? Silent overwrites, ungoverned publication of
private trails, and unverifiable claims. MemexLab inverts each: immutable sources, a
public/private boundary, and citations + evals.

## Conclusion

MemexLab is Bush's memex with the maintenance layer filled in by a governed agent — the
[lineage](../../../docs/engineering/lineage.md) this project claims, made concrete.
