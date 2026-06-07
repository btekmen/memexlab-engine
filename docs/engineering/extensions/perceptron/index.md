
# Perceptron

**The goal-aware reasoning layer for the memex engine.**
*Local-first · Markdown-conformant · Agent-operable · Multi-objective.*

> *Knowledge bases are passive. Agents are reactive. The Perceptron is the active layer in between — it knows what `<operator>` wants, watches every entity, and surfaces the right one at the right moment with the right rationale.*

---

## 1 · One-paragraph product

**Perceptron** is an ML/agent extension to the [MemexLab Engine](https://btekmen.github.io/memexlab-engine/) that learns `<operator>`'s goals, scores every entity in the vault against those goals along multiple axes simultaneously, and exposes the result through the engine's existing MCP server so that any agent — Claude, a custom operator, a workflow runner — can ask *"who/what do I know that matters for this, right now, and why?"* and get a sourced answer in one call. It does **not** replace the vault. It does **not** replace the engine. It is the reasoning substrate that makes a 20,000-entity second brain feel like a chief-of-staff.

---

## 2 · The problem

Every personal knowledge management system follows the same arc:

1. **Year 1.** Excitement. Beautiful daily notes. Books indexed. Atomic ideas linked.
2. **Year 2.** The vault grows past a thousand entities. Search returns sensible results. Graph view is mesmerizing.
3. **Year 3+.** Scale crisis. Twenty thousand entities. You know they're in there, but you can't find the *right* one. Search returns ten correct results when you needed *the* one. The brain becomes a museum: impressive, navigable, useless.

Agents make this worse, not better. A naïve agent over a large vault retrieves widely and synthesizes ungroundedly. It can find anything — and so it surfaces things at random, dressed up as relevance.

What's missing is a **layer that knows the operator's current objective** and ranks entities against it with a defensible rationale. Not search ("what is this?"). Not chat ("what should I think?"). **Reasoning** ("what should I act on?").

V0 of this product, [[network-perceptron]], demonstrated this for a single goal (a single operator's BD pipeline) over a single entity type (contacts). It went from ~1,800 vault entities to ~24,000 in a session, with a thousand strong-tie targets ranked along four product-fit dimensions. The operator went from *"who in my network?"* to *"Person X, rank 46, score 0.84, product-fit 1.0, here's why"* in one MCP call. That's the workflow Perceptron generalizes.

---

## 3 · The thesis

Three convictions drive the product:

**3.1 Knowledge graphs are infrastructure; reasoning is the product.**
The vault is plumbing. The engine is the operating system. The Perceptron is the application layer that turns infrastructure into leverage. The engine controls the rails (markdown, slugs, edges, embeddings); Perceptron controls the cargo (goal-aware scoring, rationales, briefings).

**3.2 Goals are the missing primitive in PKM.**
Every existing PKM ontology has notes, tags, links, types. None of them has a first-class object for **"what am I trying to do right now."** Without it, scoring is meaningless. Perceptron makes the **goal** a typed entity with its own lifecycle, its own training set, and its own product-fit vector.

**3.3 Agents are the consumer; humans are the operator.**
The Perceptron is not a UI. It is a substrate that exposes a few sharp MCP tools (`score`, `explain`, `cluster`, `digest`) which any agent can compose into the actual interface the operator sees. The same backend powers a pre-meeting brief in chat, a daily digest in email, an outreach queue in CRM, and an active-learning prompt in the editor. **One reasoning layer, many surfaces.**

---

## 4 · Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  HUMAN OPERATOR                                                      │
│   - Defines goals                                                    │
│   - Labels edge cases                                                │
│   - Reads briefings · Takes action                                   │
└─────────────────────────────┬────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  AGENT SURFACE (Claude / custom operator / workflow)                 │
│   - Composes MCP calls into user-facing experiences                  │
│   - Pre-meeting briefs · Daily digests · Outreach queues             │
│   - Active-learning prompts · Strategic Q&A                          │
└─────────────────────────────┬────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  PERCEPTRON MCP   (the reasoning layer — this product)               │
│   - score(entity, goal)             → 0..1 + breakdown               │
│   - explain(entity, goal)           → causal rationale + edges       │
│   - rank(query, goal, k)            → top-k entities for a goal      │
│   - cluster(goal, by)               → typed segments / cohorts       │
│   - digest(goal, since)             → narrative summary              │
│   - propose_labels(goal, k)         → active-learning queue          │
│   - calibrate(goal)                 → trains/updates the model       │
└─────────────────────────────┬────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  MEMEXLAB ENGINE   (existing — unchanged)                            │
│   - Vault (markdown, slugs, frontmatter, edges)                      │
│   - reindex, reembed, resolve, search                                │
│   - MCP server                                                       │
└─────────────────────────────┬────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  SOURCE PLANE   (entity ingest — expanded)                           │
│   - Contacts (LinkedIn / Mac / iCloud / vCard)                       │
│   - Conversations (Slack / Discord / Telegram / WhatsApp via export) │
│   - Email (Gmail / IMAP — headers + selected bodies)                 │
│   - Calendar (Google / Apple — events as edges)                      │
│   - Code (GitHub — stars, PRs, follows)                              │
│   - Reading (Matter / Readwise / Kindle / Pocket)                    │
│   - Long-form (Twitter / X / Bluesky / Substack)                     │
│   - Audio (Granola / Otter / Fireflies transcripts)                  │
│   - Documents (Drive / Notion / Dropbox / Box — selective)           │
│   - Location (timeline export — strictly opt-in)                     │
└──────────────────────────────────────────────────────────────────────┘
```

**Key design constraints, in order of importance:**

1. **Engine is sacred.** No changes to the engine. Perceptron is additive.
2. **Vault is source of truth.** Every score, rationale, label is materialized into markdown (in `_perceptron/` atomic folder) so the vault is recoverable without the Perceptron service.
3. **Local-first.** No data leaves the operator's machine without an explicit opt-in per goal. The engine's no-cloud / no-lock-in posture is preserved.
4. **Agent-operable by default.** Every Perceptron capability is an MCP tool first. UIs are optional consumers, not load-bearing.
5. **Schema-conformant.** Goals, scores, rationales, labels all use AtomicFrontmatter — they validate cleanly with `memex reindex`. The Perceptron's own state is itself a queryable part of the brain.

---

## 5 · The goal layer

The pivotal new primitive. A **goal** is a typed entity in `<your-vault>/goals/` (new top-level folder, accepted by the engine as `goal` curated type via a small ontology extension).

```yaml
---
title: <Your Goal — Vertical Q3 2026>
type: goal
created: 2026-04-30
updated: 2026-05-02
status: active
horizon: Q3-2026
owner: <operator-slug>
tags: [<your-company>, bd, <vertical>]
objective: >
  Identify and engage 50 senior-executive prospects matching <ideal-profile>
  for <your-product> onboarding by end of Q3.
success_metric: 50 first-meetings booked
deal_value_signal: high
ideal_entity_profile:
  - type: person
    seniority: >= 0.85
    in_target_company_tier: true
    strong_tie: preferred
  - type: company
    industry: ["<industry-1>", "<industry-2>", "<industry-3>"]
    public_listed: preferred
anti_targets:
  - "Direct competitors"
  - "Companies in active distress"
weighting_hints:
  founder: 0.1
  target_company_tier: 0.4
  strong_tie: 0.3
  recent_interaction: 0.2
provenance:
- claim: "Defined in coordination with the <your-team> April 2026."
  source: "[[<your-team>]]"
---
```

**The goal does four things at once:**

1. Declares an objective in natural language *and* in structured constraints (the `ideal_entity_profile` is the model's bias).
2. Anchors a labeling set — labels are versioned per goal, not global.
3. Defines a horizon (so the model knows when to refresh).
4. Names success criteria so the system can measure itself.

**Multiple goals coexist.** An operator may simultaneously run "BD" + "Hiring" + "Fundraising" + "Reading list curation" goals. The Perceptron scores every entity against every active goal and surfaces a **multi-objective vector**, not a single number. The agent decides which axis to project on for any given query.

This is the **multi-product fit vector** generalized — V0 had four vertical product-fit axes; V1 has N user-defined goals, each a learnable dimension.

---

## 6 · The source plane

The engine already accepts arbitrary entities. Perceptron expands the **ingest catalog** — opinionated importers for the sources that most often hold latent entities.

Each importer lands raw notes in `<your-vault>/raw/<subtype>/` (engine-conformant) and emits curated person/company/conversation entities to the appropriate folder. The set:

| Source | Yields | Privacy posture |
|---|---|---|
| LinkedIn CSV / Sales Navigator | persons + companies | local only |
| Mac Contacts (.abbu / vCard) | persons + numbers | local only |
| iCloud / Google Contacts | persons | local only |
| Twitter / X archive | follows · followers · DM partners | local only |
| Gmail (via OAuth or .mbox) | recipients + reply graph | selective — headers default, bodies opt-in |
| Google Calendar | event-attendees as edges | local only |
| Slack / Discord export | conversation graph | local only |
| Granola / Otter / Fireflies | meeting transcripts + people | local only |
| GitHub | stars · follows · PR co-authors | local only |
| Matter / Readwise / Kindle | books · highlights · authors | local only |
| Apollo / Clay (CRM) | enrichment overlays | API key, local cache |
| ZoomInfo / SimilarWeb (sales MCPs) | firmographics | API key, local cache |

**The opinion:** every importer is **append-only** into `raw/`. Compilation into curated entities is a deterministic, replayable step. The operator can prove what the system knows and re-derive it from sources.

The Perceptron exposes a single ingest command:

```bash
memex perceptron ingest --source linkedin --since 2026-01-01
memex perceptron ingest --source gmail --since 2026-04-01 --headers-only
memex perceptron ingest --source matter --all
```

---

## 7 · The model

A composition, not a single algorithm. **Three layers** with sharp boundaries.

**7.1 Feature plane** (deterministic, transparent).
Per-entity features computed from frontmatter, edges, and source-overlay data. Examples for persons: seniority parse (locale-aware), founder/owner flag, company tier (organization-tier lookup), source diversity, relationship strength (cross-source presence), recency-of-interaction, role/function. For other entity types: domain (book), author cluster, publication date (article), recency (note), citation count (concept). **Every feature is human-readable and writeable back into the entity frontmatter** so the rest of the engine can use it without the Perceptron.

**7.2 Goal-conditional scorer** (learned per goal).
A small model — logistic regression / gradient-boosted tree / single-layer MLP, the operator's choice — trained on **the goal's labels** with the feature plane as input. Crucially: blended with the goal's `weighting_hints` as a domain-knowledge regularizer. The V0 lesson holds: with few labels, **encode prior beliefs as a partial weight regularizer** so the model can't degenerate.

**7.3 Explainer** (causal rationales).
Every score is paired with a **why**: which features fired, which edges contributed, which goal weightings tipped it. The explainer is not a SHAP wrapper — it's a structured object the agent can verbalize: *"Person X scores 0.84 for `<goal>` because (1) seniority=0.95 [\<Senior Title>], (2) target_company_tier=true [\<Target Company>], (3) strong-tie=true [present in two source channels], (4) goal weighting_hint emphasizes company tier + strong tie."*

**Multi-objective:** the score for entity *e* is a vector *s* = [s_g1, s_g2, ..., s_gN] across all active goals. The `rank()` MCP tool takes a goal id and projects onto that axis; `score()` returns the full vector; `cluster()` does k-means or community detection across selected dimensions.

**Active learning loop.** After each scoring run, `propose_labels()` returns the entities the model is **most uncertain about within the operator's likely target band** (high enough heuristic to matter, low enough confidence to learn from). Five labels per session, weekly, indefinitely. The model gets sharper with use.

**Drift detection.** Every time `calibrate()` runs, it logs (in `_perceptron/calibration-log.md`) the CV AUC, label balance, top-weight features, and the entity-set version. The operator can see the model's posture change over time and roll back if needed.

---

## 8 · The interface

**8.1 MCP surface (canonical).** Seven tools, no more:

| Tool | Returns |
|---|---|
| `score(entity_id, goal_id?)` | Per-goal score vector with feature breakdown |
| `explain(entity_id, goal_id)` | Structured causal rationale (features + edges) |
| `rank(query?, goal_id, k, filters?)` | Top-k entities for goal, with mini-explanations |
| `cluster(goal_id, by?)` | Typed segments (cohorts / strategic groups) |
| `digest(goal_id, since?)` | Narrative summary of changes / new high-scorers / actions taken |
| `propose_labels(goal_id, k=5)` | Active-learning queue with uncertainty rationale |
| `calibrate(goal_id, labels?)` | Retrain + post diagnostics; idempotent |

**8.2 Generative surfaces (built on the MCP).** Reference implementations the project ships, all derived from the seven tools:

- **Daily digest** — `digest(active_goals, since='yesterday')` rendered as a markdown brief in the inbox folder, summarizing: highest-movers per goal, new high-scorers, action queue.
- **Pre-meeting brief** — `rank(query=attendee_name, goal=meeting_context, k=1)` + `explain()` rendered as a one-page card.
- **Outreach queue** — `rank(goal=BD, k=20, filters=[no-touch-in-90d])` → exported to Apollo/HubSpot/Close via the sales-MCPs.
- **Active labeling card** — `propose_labels()` rendered as an editor/web mini-form with 1/0/skip keyboard shortcuts (the V0 labeling tool, generalized).
- **Weekly review** — `cluster(goals=all, by='cohort')` + `digest()` rendered as a Sunday-evening retrospective.

**8.3 Vault materialization.** All Perceptron outputs are also markdown files:

```
<your-vault>/
├── goals/                              ← NEW: goal entities
│   ├── <your-goal-1>.md
│   ├── <your-goal-2>.md
│   └── <your-goal-3>.md
├── _perceptron/                        ← NEW: atomic outputs
│   ├── calibration-log.md
│   ├── digests/2026-05-02.md
│   ├── rankings/<your-goal-1>-top100.md
│   ├── labels/<your-goal-1>.csv
│   └── feature-importance.md
└── people/<slug>.md                    ← EXISTING — score field added
```

Every entity gets a `perceptron:` block in its frontmatter:

```yaml
perceptron:
  scores:
    <your-goal-1>: 0.84
    <your-goal-2>: 0.18
  last_calibrated: 2026-05-02
  features_version: 3
```

The vault is recoverable to its full state without the Perceptron service running. Anything Perceptron writes is markdown.

---

## 9 · The loop

V0 was a one-shot. V1 is a **continuous loop** with five phases:

```
       ┌─────────────────┐
       │ 1. INGEST       │  daily — pull new entities from sources
       └────────┬────────┘
                ▼
       ┌─────────────────┐
       │ 2. ENRICH       │  feature plane recomputed for new entities
       └────────┬────────┘
                ▼
       ┌─────────────────┐
       │ 3. SCORE        │  apply each active goal's model to every entity
       └────────┬────────┘
                ▼
       ┌─────────────────┐
       │ 4. SURFACE      │  digests + briefings + outreach queues
       └────────┬────────┘
                ▼
       ┌─────────────────┐
       │ 5. CALIBRATE    │  operator labels 5 propose_labels candidates
       └────────┬────────┘
                │
       ┌────────┘
       │ retrain affected goals; log to calibration-log.md
       └───── loop
```

A **cadence config** lets the operator set per-step frequency. Default:

| Step | Default cadence |
|---|---|
| Ingest | daily, 04:00 local |
| Enrich | daily after ingest |
| Score | daily after enrich |
| Surface (digest) | daily 07:00 (in time for morning) |
| Surface (briefings) | event-driven (calendar trigger) |
| Calibrate | weekly Sunday + on-demand |

---

## 10 · The product surface

The operator sees five things. Everything else is plumbing.

1. **The Goal Dashboard** — list of active goals, their progress, their model health, their next labeling card. (One page, web.)
2. **The Morning Digest** — markdown brief delivered to inbox at 07:00. Top movers, new high-scorers per goal, three suggested actions. (Email + editor.)
3. **The Briefing-on-Demand** — for any upcoming meeting, ask any agent ("brief me on X"), get a one-page card. (Chat.)
4. **The Outreach Queue** — top N candidates for the active BD goal, with reasons, exported to CRM. (CRM + email.)
5. **The Active Label Card** — five entities per week the model wants the operator to label. Two minutes. (Web.)

Everything is **markdown-recoverable**. Everything is **agent-callable**. The operator can ignore the UIs and live in chat; or ignore chat and live in the editor; or wire it into a spreadsheet. The Perceptron is the same regardless.

---

## 11 · Roadmap

| Version | Date | Scope |
|---|---|---|
| **V0** (`network-perceptron`) | shipped May 2026 | One operator. One goal. One entity type (contacts). ~21K entities materialized into the vault. Blended perceptron + heuristic. CV AUC 0.82. Excel + dashboard + curated index pages. |
| **V0.5** | Q3 2026 | Generalize ingest beyond LinkedIn+Mac+Twitter. Add Gmail headers + Calendar + meeting-transcript importers. Add second goal type (hiring). Materialize scores into entity frontmatter. |
| **V1** | Q4 2026 | Multi-objective scorer. Goal entities (typed). Active-learning loop. Vault-resident calibration logs. MCP surface (7 tools). Reference daily digest. |
| **V1.5** | Q1 2027 | Causal explainer with edge-attribution. Cluster analysis (typed cohorts). CRM exports. Built-in importers for top 12 sources. |
| **V2** | Q2 2027 | Embedder upgrade (sentence-transformers or domain-tuned). Goal templates marketplace (BD / fundraising / hiring / research / reading curation). Open-source release. Documentation under `engineering/extensions/perceptron/`. |
| **V2.5** | H2 2027 | Federated calibration — operators can share model weights for a goal type without sharing labels or entities. Privacy-preserving aggregation. |
| **V3** | 2028 | Self-modifying goals — the Perceptron can propose new goals it notices the operator pursuing implicitly. The reasoning layer becomes generative about what *should* be measured. |

---

## 12 · Why now

Four arrivals converge:

1. **MCP is standardized.** The Anthropic MCP protocol (2024–2025) made *every* tool composable across *every* agent. Building Perceptron as MCP-native means it's instantly usable from Claude, Cursor, Cody, custom agents — without per-client adapters.
2. **PKM has scale.** A meaningful fraction of operators now have vaults with 1,000+ entities. The pain Perceptron solves is no longer theoretical.
3. **Embeddings are commodity.** Hashed-ngram, sentence-transformer, OpenAI ada — every operator can run useful retrieval. The differentiation moves UP the stack to reasoning.
4. **The agentic wave.** AI is becoming the operating system, not a feature. Perceptron is the agentic version of search.

---

## 13 · What it competes with — and what it doesn't

**Direct competitors (in spirit, not in distribution model):**
- **Clay / Apollo / Outreach** — sales tools that score *their* contacts for *the seller's* outreach.
- **Champify / Common Room / Default** — community + sales signal-graphs.
- **Refind / Glasp / Hypothesis** — reading curation with social signals.

The differentiation: **Perceptron is owned by the operator, runs on the operator's machine, uses the operator's data, and answers the operator's goals.** Clay scores leads to sell *to* you. Perceptron scores entities to act *for* you. Different sentence. Different product.

**Not a competitor:**
- **Obsidian** (the editor — Perceptron coexists)
- **MemexLab Engine** (the substrate — Perceptron extends, doesn't fork)
- **General-purpose LLMs** (the chat surface — Perceptron *feeds* them via MCP)

---

## 14 · Open questions / risks

1. **Goal sprawl.** If operators define 20 goals, the scoring vector becomes noise. **Hypothesis:** active-learning surfaces will naturally cull dormant goals; we add a `status: archived` lifecycle.
2. **Privacy of cross-source ingest.** Gmail body access is a real exposure. **Hypothesis:** headers-only by default; bodies opt-in per sender/thread; redaction layer for sensitive content.
3. **Cold-start.** A new operator has no labels. **Hypothesis:** ship goal templates (BD-generic, hiring-eng-staff, reading-strategy-classics) with seed labels + heuristic weightings; first calibrate within the first session.
4. **Embedder ceiling.** Hashed-ngram is shallow. **Hypothesis:** make embedder pluggable; ship a sentence-transformer default for V2.
5. **Single-operator vs. team.** V1 is single-operator. **Hypothesis:** for V2.5, federated calibration lets a team share a goal model without sharing data. This is the moat.
6. **Markdown materialization vs. service state.** What is canonical, the markdown or the SQLite cache? **Hypothesis:** markdown is canonical; SQLite is regenerable cache; calibration logs are markdown-first.
7. **Open source vs. proprietary.** **Hypothesis:** open-source the MCP + scorer + importers; sell hosted goal-template marketplace and (later) team federation.

---

## 15 · Anti-bets (what we will NOT do)

- **No cloud-default.** No "log in to perceptron.io" service. Local-first or it's a different product.
- **No proprietary entity format.** Everything is markdown the operator can read with `cat`.
- **No "AI inbox zero" feature creep.** Email *is* a source, not the product. We refuse to become an inbox manager.
- **No metrics theater.** Calibration logs every diagnostic; the operator sees model health, not engagement metrics.
- **No real-time scoring of every keystroke.** Batch cadence. The operator's brain isn't a debug log.
- **No goal-locked vendor relationships.** Goal templates are markdown. They can be shared as gists.

---

## 16 · Where this lives in the MemexLab Engine universe

[[memexlab-engine]] is the substrate (vault + CLI + MCP). Perceptron is one of three planned **extensions**:

- **Perceptron** (this project) — the reasoning layer
- **Compose** (planned) — long-form generative output (essays, slides, decks from the vault)
- **Beacon** (planned) — alert / notification layer (calendar-aware briefings, drift alarms)

Each extension is independently shippable, composes via MCP, and never modifies the engine. The engine remains a knowledge substrate; the extensions are products.

---

## Connections

- [[network-perceptron]] — the V0 implementation that proved the thesis
- [[memexlab-engine]] — the substrate this extends
- [[mcp-specification]] — the protocol the surface conforms to
- [[infrastructure-control]] — the architectural conviction (engine = rails, perceptron = cargo)
- [[speed-of-execution]] — the V0 → V1 → V2 cadence target

## Source material

- [[network-perceptron]] — V0 architecture, results, lessons
- MemexLab Engine docs: <https://btekmen.github.io/memexlab-engine/>
- Memex `schemas.py` — `CuratedFrontmatter` / `AtomicFrontmatter` rules that govern the materialization layer
- Active-learning literature (Bayesian uncertainty sampling)
- Anthropic MCP specification — for the canonical tool surface
- The V0 60-label calibration set — first labeling tool's localStorage export

---

*This document is the engine's extension manifesto. Generic placeholders (`<operator>`,
`<your-company>`, `<your-product>`, `<your-vault>`, `<your-goal-N>`) stand in for any
personal data, following the convention in the engine's main documentation. Render it
as a local docs page with `mkdocs serve`.*

*Status: `draft`. Next action: publish to `engineering/extensions/perceptron/` on the
docs site and open the first GitHub issue: "V0.5 — generalize ingest beyond
LinkedIn/Mac/Twitter".*
