# Memex Mark 1 Operating Core

**A sovereign operating system.**

Personal intelligence OS for a founder-operator.

---

## Core Architecture

**Memex Mark 1 Operating Core** = Graph + Evidence + Belief + Action + Governance

YOU OWN:
- Local runtime
- Markdown filesystem
- "Models are swappable. Memory is not."
- Privacy by architecture (GDPR-compatible by design)

---

## Philosophy

Every memory becomes a node.  
Every claim carries evidence.  
Every belief has a probability.  
Every meeting mutates the system.  
Every agent is governed.  
Every output drives a decision.

---

## The Operating Loop

```
Capture → Classify → Link → Pressure-test → Act → Learn
```

This is the complete loop. There is no separate deploy step. Every iteration strengthens the system, tightening the relationship between what you capture and what you decide.

---

## The Nine Layers

### 1. CORE / IDENTITY

The identity layer is not a single file — it is a quartet:

- `SOUL.md` — agent identity, tone, red lines
- `USER.md` — operator operating profile
- `MEMORY.md` — long-term agent memory
- `tekmen_memex` — curated human/strategic manifest

Together, these four components define who operates the system (agent + operator), what the agent remembers, and what the operator believes.

See [Identity Quartet](engineering/mark-1/identity-quartet.md) for details.

### 2. VAULT / GRAPH

The markdown wiki is the canonical storage layer:

- Markdown filesystem (`[[slug]]` wikilinks)
- Entity graph (people, companies, concepts, philosophies)
- GBrain/Mark1 query interface

The vault is the database. Every entity is a node. Every wikilink is an edge.

### 3. EVIDENCE / REALITY

Every major claim binds to reality. Evidence exists in one of four field-states:

- **Not tracked** — no evidence layer exists yet
- **Tracked but unavailable** — we know we need it, but don't have it
- **Available but needs owner approval** — evidence exists, pending human review
- **Definition unresolved** — the claim itself is not yet well-formed

**Surfaces:**
- `[[reviews/evidence-inbox]]` — incoming evidence for triage
- Platform economics dashboard
- Core advantage benchmark
- Agentic workflow map

### 4. JUDGMENT / BELIEF

Every belief has a probability and a deadline:

- `[[ledgers/prediction-ledger]]` — probability + deadline per claim
- `[[registers/strategic-risk-register]]` — named risks with mitigation status
- Counter-thesis documents — the strongest case against our position
- Monthly calibration — update probabilities based on new evidence

Beliefs are not permanent. They are tested, updated, and sometimes reversed.

### 5. ACTION / APPROVAL

Every action requires owner approval. No external outreach happens without human review.

- `[[registers/stakeholder-move-register]]` — owner / metric / due / escalation
- Meeting-as-transaction: 3 facts, 1 changed belief, 1 next action
- Human approval required for boundary-crossing actions

This is the **Action / Approval** layer, not "Action / Stakeholder."

### 6. AGENT RUNTIME

Seven named agents, each with bounded scope:

1. **Archivist** — schema / link hygiene
2. **Analyst** — synthesis / brief
3. **Skeptic** — counter-thesis
4. **Decision** — ledger / risk / postmortem
5. **Relationship** — network activation
6. **Strategic Watch** — watches the world
7. **Chief-of-Staff** — agenda / decision / action

**Under development (not shipped):**
- Agent Black Box Recorder — audit log for every agent action

### 7. MODEL ROUTER

Models are swappable. The router dispatches based on task profile:

- **GPT** (OpenAI) — general reasoning, structured outputs
- **Claude** (Anthropic) — long-context retrieval, citation-heavy work
- **Z.ai** — domain-specific fine-tunes
- **DeepSeek** — cost-optimized batch processing
- **Qwen local** — private, air-gapped inference

Modes:
- Cheap batch (high volume, low risk)
- Strong reasoning (complex decisions, high stakes)
- Local-private (sensitive data, no external API)
- Domain evals (task-specific benchmarks)

**Under development (not shipped):**
- Model Treasury — cost tracking, performance logging, automatic fallback

### 8. FIREWALL

Six grades of data classification replace the old four-class model. Every note is assigned a grade; every output respects it.

| Grade | Description | Example |
|-------|-------------|---------|
| **Personal private** | Never leaves the vault | Health records, family notes |
| **Company private internal** | Restricted to team | Strategy memos, financial models |
| **Investor-ready** | Approved for fundraising | Pitch decks, term sheets |
| **Regulator-safe** | Can withstand audit | Compliance docs, audited claims |
| **Public content** | Already published or publishable | Blog posts, open-source docs |
| **Group chat safe** | OK for Slack/Discord | Logistics, scheduling, links |

Human review is required at every boundary crossing.

**Under development (not shipped):**
- Disclosure Compiler — automatic grade assignment and redaction

See [Firewall & Data Classification](engineering/mark-1/firewall.md) for the full policy.

### 9. OUTPUT SURFACES

Every output is a first-class note in the vault, carrying metadata, sources, and grade:

- **Founder Operating Console** — daily dashboard: open loops, decisions pending, calendar analysis
- **Board/Investor Brief** — quarterly narrative with evidence links
- **Meeting Briefs** — pre-meeting context: who, why, what changed, one sharp question
- **Proof Sprint Sheet** — hypothesis → test → result tracker
- **Relationship Activation Briefs** — who to reach, why now, best opening
- **Weekly Anti-Narrative Review** — what we believed last week that we no longer believe
- **Postmortems** — what happened, what we thought would happen, what we learned

Every output cites its sources by `[[slug]]`. Every output lives in the vault and is linkable, searchable, retrievable.

---

## Under Development (Not Shipped)

The following components are **not yet implemented** in the CLI or engine. They are design targets, not shipping features:

### Compilers

- **Belief Compiler** — converts raw claims into calibrated probabilities
- **Evidence Compiler** — binds claims to sources and tracks field-state
- **Disclosure Compiler** — auto-classifies notes into firewall grades
- **Model Treasury** — cost tracking, latency logging, automatic provider fallback
- **Agent Black Box Recorder** — audit trail for every agent action
- **Relationship Radar** — network state tracker with scoring and activation signals

### Modes

Named operational modes that change system behavior:

- **War Room** — rapid iteration, all gates open, human-in-the-loop on every output
- **Board** — formal mode for board materials: strict evidence, high-confidence claims only
- **Regulator** — compliance-first: every claim is auditable, every source is retained
- **Investor** — fundraising mode: optimistic tone, forward-looking, approved deck only
- **Founder Mirror** — reflection mode: what changed, what didn't, what should have

### Meters (Five)

System health and performance metrics:

1. **Trust Score** — how often predictions resolve correctly
2. **Open Loop Severity** — count and age of unresolved questions
3. **Execution Debt** — actions committed but not completed
4. **Belief Drift** — rate of change in stated probabilities
5. **Network Perceptron Score** — relationship graph health and activation readiness

**Network Perceptron Score** is a **meter**, not a compiler.

---

## How This Differs from the Current Implementation

### What Ships Today

**`memex-cli` (0.1.0)** — ingest-spine + retrieval + qa:
- `ingest url|kindle|readwise|rss|youtube-feed|feeds|youtube` — bring sources into the vault
- `view` — list views or view members (saved queries)
- `search` — deterministic BM25 keyword search or hybrid (with embeddings)
- `qa` — ask a question, get a `[[slug]]`-cited answer
- `reindex` — build/refresh the local semantic index (a rebuildable cache)

**`memexlab-mcp`** — governed local memory for AI agents (MCP server, 6 tools):
- `vault_info` — vault overview (note count, sections, write dir, views)
- `search_vault` — deterministic BM25 search with `[[slug]]` citations
- `read_note` — read one note by slug or path
- `capture_note` — governed write into inbox/ with provenance
- `list_queue` — read-only view of the task queue
- `complete_queue_item` — complete a queue task and file the result

### What Is NOT Shipped

The CLI commands described in §§00–15 (`doctor`, `migrate`, `rollback`, `compile`, `lint`, `index`, `export essay|slides`, `chart`) are **not implemented**. Those sections describe a parallel design (the "eight modes" model) that has not been built. The actual CLI is ingest + retrieval + qa.

**Mark 1 Operating Core** is the conceptual architecture that both the CLI and the §§00–15 manual are evolving toward. The nine layers describe the **destination**, not the current state.

Most importantly:
- The seven named agents are **design spec**, not running code.
- The compilers, modes, and meters are **not shipped**.
- The firewall six-grade model is **policy**, not enforcement (yet).
- The output surfaces exist as **templates**, not automated workflows.
- The MCP tool names in older docs (`brain_status`, `resolve_link`, `read_entity`, etc.) are from a prior design and do not match the shipped MCP server.

### Two Manuals, One Destination

This documentation contains **two world-models**:

1. **§§00–15** — the "eight CLI modes" model (`inbox/raw/wiki`, `doctor/migrate/compile/lint/qa/index/export/chart`)
2. **Engineering pages** — a second vocabulary (`content/sources|items|maps`, ETCLOVG, Fast/Standard/Strict, GBrain, `brain_status` MCP tools)

Neither matches the shipped CLI (`ingest/view/search/qa/reindex`) or MCP server (`vault_info`, `search_vault`, `read_note`, `capture_note`, `list_queue`, `complete_queue_item`).

**Mark 1 Operating Core** is the north star that resolves this drift. Treat §§00–15 and the engineering pages as **design sketches**, and the CLI/MCP as **shipping reality**. This document describes where all three are converging.

---

[← Future Expansion](14-future-expansion.md) · [Docs index](README.md) · [Identity Quartet →](engineering/mark-1/identity-quartet.md)
