---
name: memex-brief
description: Produce pre-meeting or decision briefs from a memex with ranked entities, cited context, and recommended questions.
---

# Memex Brief

## Workflow

1. Resolve meeting subject to entities.
2. Retrieve people, companies, relationships, decisions, and sources.
3. Rank what matters now. For a morning brief, call `plasticity(policy="rps")` or `memex plasticity rps`. The score is a weighted mean with a per-factor breakdown. It does not edit the vault.
4. Produce a short brief: context, risks, openings, sharp questions.
5. Cite every material fact.
