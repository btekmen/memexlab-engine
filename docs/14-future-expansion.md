# Future Expansion

The current system is deliberately single-operator, single-vault, local-first. This is an engineering choice, not a limit — the constraints make the core engine small, predictable, and trustworthy. But the architecture admits several expansions that would extend the system without compromising its foundations.

This page describes those expansion paths. None are built today. Each is designed so that building it would not require rewriting the core.

## The rule that constrains every expansion

Whatever extends this system must preserve four invariants:

- The filesystem is the database. Any new feature that introduces a second source of truth (a sidecar SQL store, a remote vector index that isn’t reproducible from the vault) violates the contract. The vault is the canonical state.

- Plain markdown is the storage layer. New features may add metadata, but the body of a note remains human-readable markdown that opens correctly in any editor without the engine running.

- Dry-run-by-default is universal. Every mutating feature supports a dry-run that shows exactly what would change. Every `--apply` requires explicit invocation.

- The LLM is additive, never load-bearing. The vault must remain fully usable without LLM calls. The LLM accelerates; it does not gate.

Any expansion that compromises these four invariants does not ship.

## Expansion: multi-user / shared team knowledge

What it is. A second operator — or a small team — reads from the same vault, and some write to scoped folders.

What changes. Adding collaborators requires:

- A `contributors/` directory with one note per collaborator, listing what they can touch.

- Per-folder ownership declarations in the engine config, defaulting to single-owner.

- A git-based pull-request workflow for any change outside a collaborator’s scope.

- Contribution tagging (`contributor/jane`) so the owner can audit “what did Jane add this month?” with a single filter.

- Read-only modes for consumers who should see the vault but never write.

What doesn’t change. Schema. Tag taxonomy. Ontology. Engine commands. The first three are still owner-governed; the commands still behave the same for anyone who runs them.

Engineering shape. Almost no engine change needed. The git workflow carries most of the complexity. The engine grows one concept: a `--contributor` flag on `compile` and on the mutating commands, which stamps the resulting notes with contributor provenance and refuses to write outside declared scope.

What it’s for. A founder working with a chief of staff; a researcher working with a research assistant; a small advisory practice sharing a knowledge base across three partners.

What it isn’t for. Large-team wikis. Once you have 20 contributors, you need real access control, real merge-conflict tooling, and real governance. That’s a different product.

## Expansion: shared team knowledge with selective merge

What it is. Two or more independent vaults (say, yours and a close advisor’s) whose owners occasionally want to share specific concepts — not the whole vault, a defined subset.

What changes.

- A new `memex export share` mode that bundles a specific slug plus its transitive link closure into a shareable markdown archive with stripped sensitive frontmatter.

- A corresponding `memex import share` that reads such an archive, resolves slug collisions against the local vault, and proposes merges.

- A “shared” tag namespace (`shared/with-advisor-ahmet`) to track what has been shared outbound.

What doesn’t change. The underlying vaults remain independent. There is no cloud sync layer, no collaboration service, no dependency on any centralised system.

Engineering shape. Two new modes, roughly the complexity of `memex export essay`. The interesting work is slug conflict resolution, which the engine can handle because the schema is strict.

What it’s for. Trusted peer exchange. You and a fellow founder want to share your stablecoin-settlement thinking without giving each other full vault access.

## Expansion: API integrations for source ingestion

What it is. Automated ingestion of sources from specific systems — a Readwise highlights export, a Pocket archive, a Zotero library, a Gmail filter feeding directly to `inbox/`.

What changes.

- A new `memex ingest` mode with source-specific subcommands: `memex ingest readwise`, `memex ingest zotero`, `memex ingest pocket`.

- Each subcommand knows how to talk to one API, fetch recent items, and lay them out in `inbox/` or `raw/` with the correct template applied.

- A state file (e.g., `.memex/ingest_state.json`) tracking last-fetched timestamps per source, so re-runs are incremental.

What doesn’t change. The notes end up in the same places as if you’d captured them manually. The schema is unchanged. The rest of the workflow treats ingested notes identically to captured ones.

Engineering shape. One mode per integration. Each integration is a self-contained module under `memex/ingest/<source>.py`. Failures in one source don’t affect the others.

What it’s for. Reducing capture friction further. If you highlight in Readwise all day, you want those highlights in the vault nightly, not never.

## Expansion: bounded agent workflows

What it is. Multi-step LLM workflows that go beyond the one-prompt-one-response contract of the current engine. An example: a “weekly digest” agent that reads the past week’s new notes, identifies the three most interesting threads, and drafts a one-page summary for your review.

**Note:** The **seven named agents** (Archivist, Analyst, Skeptic, Decision, Relationship, Strategic Watch, Chief-of-Staff) are **no longer a future expansion** — they are part of **[Mark 1 Operating Core Layer 6: Agent Runtime](16-mark1-operating-core.md#6-agent-runtime)**. However, those agents are a **design specification**, not yet implemented in the CLI.

What changes.

- A new `memex agent` mode with workflow orchestration. Each workflow has: a name, a bounded task, an upper iteration count, a fixed list of allowed engine commands it may call, and a required human review step at the end.

- An agent registry under `agents/` in the vault (not in the engine) so agents can be defined per-vault.

- Strict logging — every workflow run emits one JSON event per LLM call, plus a summary event at the end.

What doesn’t change. The engine’s primitive commands. Agents compose them; they do not replace them. Also, the dry-run/apply pattern — every workflow run is a dry-run by default, producing a “proposed set of vault changes” that you review before `--apply`.

Engineering shape. Complex. Workflows mean orchestration state, retry logic, cost control, interruption handling. Not undertaken without clear evidence that named workflows outperform the existing hand-orchestrated process.

What it’s for. Bounded, recurring tasks where the manual version is high-friction and the automated version carries low risk.

What it’s not for. Open-ended “do my thinking for me.” The system’s value comes from you doing the thinking; workflows that substitute for thinking destroy the value.

## Expansion: fine-tuning on the vault

What it is. Training a smaller, cheaper model on the vault’s atomic notes so that retrieval-augmented generation is optional, not mandatory, for the simpler tasks.

What changes. Almost nothing in the vault. An export pipeline that packages wiki notes + their links as training data, a fine-tune run against a small frontier model, and a `memex qa --local` flag that routes to the tuned model for cheap questions.

What doesn’t change. The canonical prompts. The retrieval layer. The output format. Fine-tuning is an orthogonal optimisation: cheaper calls for routine queries, same calls for the heavy lifts.

Engineering shape. Straightforward if fine-tuning support exists on your chosen provider. The vault’s strict schema makes it a well-shaped training corpus; the structure is what makes fine-tuning viable.

What it’s for. Cost control, mostly. A vault that generates 50 QA calls a day against a frontier model costs real money; a vault that routes 40 of those to a fine-tuned small model costs an order of magnitude less.

What it’s not for. Replacing the frontier model on hard tasks. Compile, essay, and slides remain frontier-class operations. The fine-tune is for the 80% of queries that don’t need the big model.

## Expansion: productisation

What it is. Packaging the system for other users — a commercial or open-source product with the engine, template set, onboarding flow, and docs.

What changes. A lot, and carefully:

- Multi-tenancy — one engine, many vaults. Each user’s `.memex/` directory is private; each user’s vault is private.

- A service mode — optional hosted backend for users who don’t want to run a cron on their laptop. The core engine remains a CLI; the service layer is a thin wrapper that calls it.

- Authentication and billing — standard SaaS concerns.

- A templates marketplace — starter templates for different use cases (researcher, founder, student, consultant), with templates vetted and versioned.

- Integrations platform — the ingest layer (see above) becomes a first-class plugin system.

- Documentation-as-product — what you’re reading now becomes the published manual.

What doesn’t change. The single-vault, filesystem-as-database contract. In a hosted mode, each user’s vault is still a plain git repo they can clone and run locally. A hosted product that doesn’t let its users export plain markdown vaults is not this product.

Engineering shape. Large. Several months of work even with the engine as a starting point. Worth doing only if there is clear evidence that the user base exists and wants it.

What it’s for. Other people who think like you. The product is opinionated by design — opinionated tools have smaller audiences but more loyal users.

What it’s not for. Generic note-taking. The space is crowded. The differentiator is the opinions — atomic notes, LLM as compiler, filesystem-as-database, strict schema, dry-run-first. A productised version keeps those opinions sharp, or it has no reason to exist.

## Expansion: richer outputs

What it is. Output modes beyond the current essay/slides/chart set. Candidates:

- `memex export memo` — internal memos for specific organisational contexts (board, investors, regulators). Different tone and structure than public essays.

- `memex export thread` — social media long-form (Twitter/X threads, LinkedIn posts). Structured for the platform.

- `memex export docx` — Word document output for corporate contexts that won’t accept markdown.

- `memex export tex` — LaTeX for academic writeups.

- `memex export podcast-brief` — a structured prep doc for appearing on a podcast on a given topic (key points, likely questions, soundbites).

What changes. Each new output type is a new mode, same shape as `export essay`. Same retrieval, different prompt, different post-processing, different output folder.

What doesn’t change. The contract. Every output is a first draft, written into the vault, citing its sources by slug.

Engineering shape. Small per addition. A new prompt, a new output directory, a new post-processing step if the target format isn’t markdown.

What it’s for. Reducing the “I need to write X by Friday” friction in specific recurring formats.

## Expansion: better retrieval

What it is. The current retrieval is BM25 over tokens, with the two core notes always included. That’s deliberately simple. A stronger retrieval layer would:

- Add embedding-based similarity as a second signal alongside BM25, with an ensemble combining both.

- Support semantic clustering for `memex chart` — a “concept map” chart that shows which notes cluster together by meaning, not just by tags.

- Handle query expansion — automatically rewriting “DNS” to `deferred-net-settlement` during retrieval.

- Respect temporal context — a query about “current regulatory posture” gets newer notes preferentially.

What changes. The `memex.retrieval` module grows. Embeddings get cached to `.memex/embeddings/` with hashes so they invalidate correctly on note changes. The engine runs embedding generation on a new `memex reindex` command.

What doesn’t change. The output contracts. Every LLM call still receives a bounded list of notes as context; the retrieval layer just picks a better list.

Engineering shape. Moderate. The harder engineering is cache invalidation, not embedding itself.

What it’s for. Cases where BM25 misses — synonyms, acronyms, conceptual similarity without shared tokens. Currently you work around these with explicit search terms; a better layer lets the engine work around them for you.

## Expansion: in-editor integration

What it is. An Obsidian plugin that exposes engine commands inside the editor. You select a block of text in a raw file and pick “Compile selection” from the command palette; the plugin runs `memex compile --selection` under the hood, shows the dry-run inline, and offers “Apply” and “Revise” buttons.

What changes. A new Obsidian plugin under `plugins/memex-editor/`, talking to the engine via CLI spawn.

What doesn’t change. The engine itself. Every plugin operation maps 1:1 to an existing CLI invocation.

Engineering shape. Plugin development is straightforward but tedious. Don’t undertake unless the tedium of CLI context-switching has become the dominant friction.

What it’s for. Users who never leave the editor and want every engine mode available inside it.

## Expansion: a mobile capture path

What it is. A way to capture to `inbox/` from a phone without opening Obsidian mobile, which is heavier than a capture tool should be.

Shape. A shortcut / share-sheet extension that writes a markdown file directly to the synced vault path. iOS Shortcuts + iCloud can do this today without custom code; Android options exist via Tasker or a lightweight custom app.

Engineering. Minimal. Mostly configuration, not code.

What it’s for. The single most common capture friction: you see something interesting on your phone, and the inbox is too many taps away.

## Paths we will not pursue

Some commonly-requested expansions actively conflict with the invariants and will not be built:

- Real-time collaboration (Google-Docs-style multi-cursor editing). Conflicts with the filesystem-as-database and git-based workflow. Use pull requests instead.

- Rich-text / WYSIWYG editing across the whole vault. Markdown is the storage layer; prettier editors on top are fine (Obsidian is one) but the substrate doesn’t change.

- Mandatory cloud hosting for personal use. The personal product remains local-first. Hosted is an optional tier in a productised version.

- Auto-promotion of notes. See `07-automation.md` and every other reference throughout the docs. Status transitions are manual, always.

- Opaque storage formats. Any format that can’t be grep’d, diffed, and hand-edited is excluded.

## Principles for evaluating future ideas

When a new expansion is proposed, ask:

- Does it preserve the four invariants? If no, reject.

- Is it additive or substitutive? Additive expansions extend without changing existing behaviour. Substitutive expansions change defaults. Prefer additive.

- Is the problem clearly named? An expansion motivated by “this feels limiting” is usually not ready. An expansion motivated by “I spent 2 hours/week on X and this removes that” is ready.

- Does it scale down? A feature that only makes sense at 10,000 notes is the wrong feature for a vault that today has 500.

- Can you turn it off? Every LLM call, every automation, every integration has an off switch. Features without off switches are risks.

The test for any expansion is not “is this technically impressive” but “does this extend what the vault already does, in a way that preserves trust.” Only expansions that pass that test ship.

---

[← Maintenance](13-maintenance.md) · [Docs index](README.md) · [FAQ →](15-faq.md)
