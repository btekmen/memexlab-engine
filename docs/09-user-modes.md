# User Modes

The same system serves different people in different ways. This page describes five usage profiles, each with its own priorities, typical day, and a short set of “use it like this” recommendations. You may occupy two or three of these roles at once; the guidance compounds rather than conflicts.

## Beginner user

Who. Someone new to structured note-taking, new to markdown, new to this system. Wants the value without the theology.

Priorities. - Not losing anything they capture. - A predictable place to put things. - Being able to find what they saved.

Daily rhythm. Capture into `inbox/`. Once a week, sit down for 30 minutes and walk the inbox: keep the valuable, promote to `raw/`, delete the rest. A single weekly lint pass (`memex lint`) surfaces anything structurally wrong.

Recommendations. - Start with the minimum: `inbox/`, `raw/`, `wiki/`. Ignore projects, outputs, and the curated ontology until you’ve built 50+ atomic notes. - Let templates do the frontmatter. Never hand-type a YAML block. - Don’t try to memorise the tag taxonomy on week one. Start with no tags; tags will reveal themselves by the time you have enough notes to need them. - Invoke `memex qa "..."` early and often. Watching the vault answer your questions is the single most motivating experience in this system. - Skip `export slides` and `chart` until you feel the system’s rhythm. They reward a mature vault, not an early one.

Do not. - Do not try to build a “correct” folder structure on day one. The folder structure in these docs is the correct structure; adding to it is advanced. - Do not promote anything to `evergreen` in the first month. You don’t yet know what’s evergreen.

Read next. `quickstart.md`, then `09-onboarding.md`.

## Researcher

Who. Someone whose job is thinking. Academic, analyst, strategist, policy person, investor. Accumulates hundreds of sources per year, needs to cite, needs to argue.

Priorities. - High-fidelity capture of sources, with citation metadata. - Strong link graph that mirrors the conceptual graph. - Fast retrieval for specific questions during active research. - Durable positions that survive over years.

Daily rhythm. Capture happens all day. Ingest weekly or on demand when a source matters. Compile every raw source that merits atomization. Promote atomic notes to `draft` within a week of compile. Produce on-demand — the vault exists to serve the output when the output is due.

Recommendations. - Invest in `raw/` hygiene. A researcher’s `raw/` folder is the most valuable part of the vault. Frontmatter completeness (author, venue, DOI, date) matters disproportionately here — you will cite these sources for years. - Build the ontology early and deliberately. One-page entity notes on every person, paper, and institution you cite regularly. The entity layer is what distinguishes a serious research vault from a notebook. - Use `memex index "<topic>" --type reading-order` to draft literature reviews. The output is a starting structure, not a final document — edit aggressively. - Use `memex qa` to pre-empt meeting prep. “What do I think about X?” is a question the vault can usually answer better than your working memory. - Maintain `wiki/questions/`. An open question captured today is a compounding research agenda. - Produce an essay per major topic per quarter, even if you never publish them. Essay-writing forces the vault to be complete in a way no other activity does.

Do not. - Do not let compile backlogs grow past 20 uncompiled raw files. At that point, retrieval is missing most of what you’ve ingested. - Do not rely on the LLM to summarise — use it to structure. A paragraph of your own prose is worth more in the wiki than five paragraphs of LLM paraphrase.

Read next. `04-daily-workflow.md`, `05-templates.md`, `06-metadata-and-tagging.md`.

## Founder / strategist

Who. Someone running a company or advising several. Domains interlock (Programmable Money × Islamic Finance × Regulatory Strategy × <your-company>’s roadmap × <your-product>’s market). Decisions today touch outcomes three years away. The second brain is decision-support infrastructure, not a library.

Priorities. - Low latency on “what did I think about this in Q4 last year?” - Explicit tracking of positions, not just claims. - Confidence calibration — knowing what’s firm, what’s speculative, what’s out of date. - Outputs that a cofounder or a board can actually read.

Daily rhythm. Capture in any pocket of time. Weekly inbox triage is non-negotiable. A monthly essay-writing session — even a short one — keeps the wiki honest, because essays surface gaps. Projects (`projects/<slug>/`) are the primary structure during active workstreams; the wiki is what outlasts them.

Recommendations. - Treat the ontology (`companies/`, `people/`, `philosophies/`) as your decision graph. <your-company>, <your-product>, your investors, your regulators — each gets an entity note, and each note carries the current status of your relationship or position. - Use `latticework` tags seriously. `problem-2` (deciding under uncertainty) is probably the most common one in your vault; `problem-5` (playing long games) is the most important one to pay attention to. - A position note is different from a concept note. When you write “I think X about Y,” save it as `wiki/positions/i-think-x-about-y.md` with a dated `status`. Revisit positions quarterly; promote or retire. - Use `memex export slides "<topic>" --theme gaia --apply` to generate first-draft decks for strategy discussions. The LLM won’t write the deck you want, but it will write the deck that’s easier to rewrite than to start from blank. - Run `memex chart latticework-coverage` monthly. The distribution across the five Latticework problems is a readable signal of what you’re thinking about — and what you’re not. - Never keep strategic reasoning only in email or chat. Everything important migrates to a note. Chat is a capture surface; the vault is the record.

Do not. - Do not let project folders become permanent homes for durable knowledge. When a project ends, promote. Otherwise, in two years, the wiki is empty and the projects are a museum. - Do not let <your-company>- or <your-product>-specific material live only in those entity notes. Extract the generalisable patterns into atomic notes — the entity notes should be instances of general patterns, not containers for one-off reasoning.

Read next. `10-best-practices.md`, `12-maintenance.md`, `13-future-expansion.md`.

## Operator / maintainer

Who. The person responsible for the system’s mechanics. In a one-person vault, the operator is also the owner; in a team or productised deployment, the operator might be different from the knowledge worker.

Priorities. - Structural integrity. - Reproducibility. - Observability. - Upgrade paths that don’t break the corpus.

Daily rhythm. Mostly passive: monitor `scripts/lint_daily.py` output. Monthly refactors. Respond to failure signals: a sudden spike in orphan notes, a regression in compile quality, a prompt edit that broke an output.

Recommendations. - Keep the engine on a tight version. One repo, semantic versioning, a changelog. An upgrade that breaks existing outputs should be a major version bump. - Run `memex doctor --api` at the start of every work session. Ten seconds of sanity check prevents an hour of mysterious failure. - Read `.memex/log.jsonl` weekly. Search for non-`info` events. `lint_daily_vault_error` three mornings in a row is a filesystem problem; `lint_daily_lint_error` is a schema drift. - Treat prompts as code. Changes go through the same review as code changes — diffed, tested against a held-out evaluation vault, rolled back if an output quality regresses. - Keep `.memex/snapshots/` unbounded in storage. Disk is cheap; having every migration’s pre-image for years is priceless. - Back the vault up at least weekly. Obsidian Sync is one option; `tar cz` to a remote host is another. The snapshots in `.memex/` do not substitute for a real backup.

Do not. - Do not skip snapshots because you “trust this migration”. The operator’s job is to assume nothing works until proven. - Do not edit the schema without a migration. Even an additive field needs a migration pass to ensure all legacy notes still validate. - Do not ship a change that makes past notes unreadable by the current engine. The vault must always validate.

Read next. `12-maintenance.md`, `07-automation.md`, the engine’s own `README.md`.

## Collaborator / team member

Who. Someone who reads from a shared vault (or a subset of one), may write into a scoped folder, but does not own the ontology or the schema. In the current single-operator system this mode is aspirational; it becomes relevant when the system moves toward shared team knowledge (see `13-future-expansion.md`).

Priorities. - Knowing what they can touch and what they can’t. - Not breaking the link graph. - Contributing in a way that the owner can audit.

Recommendations. - Scope collaborators to specific folders — typically a project folder or `inbox/`. Never grant write access to `wiki/`, `people/`, `companies/`, `philosophies/`, `eras/` without the owner’s explicit review of what the collaborator is adding. - Use a pull-request model even for a personal vault opened to a teammate. Every proposed atomic note is reviewed by the owner before it lands in the wiki. - Collaborators produce `raw/` material freely (they read sources and ingest them) and `inbox/` notes freely. Everything else requires triage. - Tag their contributions with `contributor/<name>` so the owner can audit “what did X add this month?” with a single filter.

Do not. - Do not run engine commands that touch the whole vault (`lint`, `migrate`, `chart`) without the owner’s knowledge. - Do not reshape the ontology. New entity types, new tag prefixes, new schema fields — these are owner decisions.

Read next. `06-metadata-and-tagging.md`, `10-best-practices.md`.

## Combining modes

Most of the time you are not purely one of these. A founder doing focused research is a researcher + strategist for that week. The operator role is usually absorbed by the owner except during upgrades or incidents.

The recommendations compound. A founder-researcher should follow the researcher guidance plus the strategist guidance; where they conflict, the strategist guidance usually wins, because the founder’s time constraint is the binding one.

A useful exercise: once a quarter, notice which mode your vault is biased toward. If the last ten outputs are all researcher-style literature reviews, you’re under-serving the strategist in you. The wiki should track what you actually need.

---

[← Automation and Scripts](08-automation-and-scripts.md) · [Docs index](README.md) · [Onboarding Guide →](10-onboarding-guide.md)
