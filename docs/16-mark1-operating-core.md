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

- `SOUL.md` — the operating mind
- `USER.md` — the operator's identity and context
- `MEMORY.md` — the memory layer's structure and governance
- `tekmen_memex` — the vault itself (the canonical slug)

Together, these four components define who operates the system, how the system operates, and what the system remembers.

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

1. **Archivist** — ingests, tags, and files new material
2. **Analyst** — retrieves, synthesizes, and drafts briefs
3. **Skeptic** — challenges claims, demands evidence, flags weak reasoning
4. **Decision** — evaluates options against stated criteria and philosophies
5. **Relationship** — tracks people, companies, and network state
6. **Strategic Watch** — monitors domains for change and signals
7. **Chief-of-Staff** — coordinates the other six, owns the weekly/monthly rhythm

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

## How This Differs from the Current CLI

The current `memex` CLI (`0.2.0-harness-preview`) implements:

- Vault storage (markdown + frontmatter + git)
- Deterministic retrieval (BM25 + basic embeddings)
- Compile mode (raw → atomic notes)
- Lint, qa, index, export commands
- MCP server (search_vault, read_note, capture_note)

**Mark 1 Operating Core** is the conceptual architecture that the CLI is evolving toward. The nine layers describe the **destination**, not the current state.

Most importantly:
- The seven named agents are **design spec**, not running code.
- The compilers, modes, and meters are **not shipped**.
- The firewall six-grade model is **policy**, not enforcement (yet).
- The output surfaces exist as **templates**, not automated workflows.

Treat this document as the **north star** for where the system is headed, and the CLI documentation (`01-overview.md` through `15-faq.md`) as the **current reality** of what ships today.

---

[← Future Expansion](14-future-expansion.md) · [Docs index](README.md) · [Identity Quartet →](engineering/mark-1/identity-quartet.md)
