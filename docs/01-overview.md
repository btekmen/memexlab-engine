# Overview

## What MemexLab is

MemexLab is a personal knowledge operating system. It is an Obsidian-first, markdown-native vault with a small, deterministic CLI engine that compiles raw sources into atomic knowledge, maintains a linked canonical layer, and produces durable outputs — essays, slide decks, and structured indexes — that feed back into the same vault.

It is one vault, one corpus, one set of opinions about knowledge, operated by one person. It assumes no server, no database, and no sync service beyond the filesystem. Every note is a plain markdown file. Every transformation is reproducible from the inputs alone.

## What problem it solves

The working memory of a serious thinker — an investor, founder, regulator, researcher — is under constant pressure from volume and time. Three specific failures are common:

- Context collapse. A position developed carefully over six months is re-derived from scratch at the next meeting because the working notes were lost in a chat thread, a Notion page, or a one-off document.

- Shallow retrieval. What you can find is a fraction of what you once understood. The retrieval tool is the search bar, the unit of return is the file, and there is no concept of a claim, a source, or a position.

- Drift. Without explicit structure, long-running themes — Programmable Money, AI-Native Banking, Stablecoin Settlement, Islamic Finance — blur into one another across thousands of fragmentary notes.

MemexLab is the answer to all three at once. Capture is cheap. Compilation is a named step with its own output. The canonical layer is small, curated, and linked. Retrieval is a deterministic search over a reproducible corpus, not a guess across a chat history. Outputs are first-class notes — they live in the vault, carry metadata, and participate in the same link graph as their sources.

## What makes it different from ordinary note-taking

Atomic notes, not documents. A canonical note carries one claim, one concept, or one entity. It is roughly 200–1200 words. Anything longer is a project note or an output, not a wiki note. Atomicity makes notes re-linkable without cascading rewrites.

Compilation is separate from capture. Capture is fast, noisy, and permissive. Compilation is slow, structured, and model-assisted. The boundary between raw and canonical is explicit — you can see, at any moment, which sources have been processed and which have not.

LLMs compile; humans decide. Claude does the mechanical work of cutting a long source into candidate atomic notes, drafting answers to research questions against the vault, or proposing an index over a topic. Every LLM output is a proposal, not a commit. The operator reviews and applies.

Deterministic by default. The retrieval layer is BM25, not embeddings. Lint is rule-based. Charts are computed from frontmatter. Re-running the same query against the same vault produces the same result. Non-determinism is isolated to the LLM calls themselves, and the surrounding pipeline is logged and reproducible.

The filesystem is the database. There is no separate index to rebuild, no migration to run when the schema changes. If you can read the markdown files, you have the system. If Obsidian disappears tomorrow, the vault is portable to any editor that reads UTF-8 text.

The engine is additive, not authoritative. You can delete the CLI, keep the vault, and you still have a working knowledge system. The engine accelerates maintenance and generation; it does not own the content.

## Core design philosophy

- Plain text forever. Every file is UTF-8 markdown with YAML frontmatter. No proprietary formats. No lock-in.

- Small surface area. Seven folders, three frontmatter schemas, eight CLI modes. You can hold the whole system in your head.

- Narrow rules, strictly applied. The system works because the constraints are enforced — by the schema, by the linter, by the compiler. Loosening a rule “just this once” is how vaults decay into dumping grounds.

- Dry-run by default. Every destructive CLI operation prints its plan and exits. Nothing is written until `--apply` is passed. Every apply takes a snapshot first.

- The human is the final reviewer. No LLM output is committed without a human read. The engine is a force multiplier, not an autonomous agent.

- Compounding, not completeness. The vault is never done. The goal is to accumulate durable, linkable knowledge over a decade, not to exhaustively cover any single topic.

- Turkish and English are first-class. Casefold-correct dotted/dotless-i handling, UTF-8 throughout, transliteration for slugs. No monolingual assumptions.

## What MemexLab is not

It is not a note-taking app. It is not a writing app. It is not a CRM, a task manager, a reading list, or a journal. It is not a team wiki. It is not real-time. It does not do automatic summarisation on capture. It does not embed, cluster, or recommend.

It is the stable substrate on top of which those things can be built, if needed, without losing the data.

---

[← MemexLab in One Page](00-one-page.md) · [Docs index](README.md) · [Architecture →](02-architecture.md)
