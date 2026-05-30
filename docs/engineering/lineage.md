
# Lineage and Credits

Memex stands on a clear lineage. The first and most important credit goes to Andrej Karpathy's LLM Knowledge Bases / LLM Wiki pattern.

## Primary credit: Andrej Karpathy

Karpathy's **LLM Knowledge Bases** framing defines the core move this project builds on: use LLMs to maintain a personal knowledge base as a persistent artifact, not as a disposable chat transcript or one-shot RAG answer.

His **LLM Wiki** gist gives the clearest operating pattern:

- raw sources are preserved as immutable evidence
- the LLM maintains a structured markdown wiki between the user and the raw sources
- new sources update existing entity, topic, and synthesis pages
- contradictions, cross-references, indexes, and logs are maintained over time
- answers can become new wiki pages, so inquiry compounds inside the knowledge base

Memex adopts this core thesis directly: the wiki is a compiled layer of knowledge, and the LLM is the maintainer.

References:

- Andrej Karpathy, **LLM Knowledge Bases**, X thread: https://x.com/karpathy/status/2039805659525644595
- Andrej Karpathy, **LLM Wiki**, GitHub gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

## Operational influence: Garry Tan

Garry Tan's **GStack** and **GBrain** informed the operational shape around the Karpathy wiki pattern.

Thank you to Garry Tan for developing and sharing both GStack and GBrain. Those projects make the agent-operable version of this idea much more concrete: GStack shows how to package durable agent workflows, and GBrain shows how to turn a markdown knowledge base into a searchable, cited, graph-aware brain layer.

**GStack** demonstrates a markdown-native agent operating system: explicit roles, repeatable skills, review workflows, QA, security checks, release routines, and a disciplined way to turn an AI coding agent into a structured software team.

**GBrain** demonstrates the retrieval and brain layer: a local-first agent brain with synthesis, citations, graph traversal, gap analysis, PGLite storage, embeddings, and autonomous maintenance workflows.

Memex borrows from these projects at the architecture level:

- skills as durable workflow contracts
- retrieval that returns cited synthesis rather than only ranked chunks
- graph-aware memory rather than flat note search
- health checks, evals, and benchmarks as operating requirements
- local-first files plus machine indexes as complementary layers

References:

- Garry Tan, **GStack**: https://github.com/garrytan/gstack
- Garry Tan, **GBrain**: https://github.com/garrytan/gbrain/tree/master

## What Memex adds

Memex is not trying to hide its influences. Its job is to package the lineage into a public-ready framework that can be audited, forked, and adapted without leaking a private vault.

The additions here are:

- a public/private repository boundary
- typed entity and item schemas
- reusable templates for sources, items, decisions, relationships, and reviews
- Agent Skills-compatible workflows for ingest, query, markdown edits, briefs, and evals
- validation scripts and CI for index and fake-vault quality
- governance rules for provenance, privacy, and publication
- benchmark rubrics for retrieval, citation quality, synthesis, contradiction handling, and privacy

## Attribution policy

Future documentation should preserve this order of credit:

1. Andrej Karpathy for the LLM Knowledge Bases / LLM Wiki pattern.
2. Garry Tan for GStack's agent-workflow discipline and GBrain's retrieval/brain architecture.
3. This Memex repository for the packaged framework, templates, governance, evals, and public/private deployment model.

When describing the project externally, use this concise wording:

> Memex is a local-first, agent-operable second-brain framework inspired first by Andrej Karpathy's LLM Knowledge Bases / LLM Wiki pattern, and operationally influenced by Garry Tan's GStack and GBrain.
