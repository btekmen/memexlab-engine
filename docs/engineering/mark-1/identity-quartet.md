# Identity Quartet

The identity layer in **Memex Mark 1 Operating Core** is not a single file. It is a quartet of four components that together define who operates the system, how the system operates, and what the system remembers.

---

## The Four Components

### 1. SOUL.md

Agent identity, tone, red lines.

This defines:

- Voice and tone (dense, decisive, sourced)
- Citation discipline (`[[slug]]` syntax, no invented facts)
- Retrieval strategy (resolve before search, read before answer)
- Red lines — what the agent will never do

The soul is the agent's **identity**.

**Current state:** Implemented in `memexlab-mcp` as the base system prompt. See [Agent Soul](../agent-soul.md) for the template.

---

### 2. USER.md

Operator operating profile.

This file contains:

- Name, role, and primary organization
- Active projects and goals
- Strategic philosophies (the frameworks that shape decisions)
- Domain focus (industries, technologies, regulatory contexts)
- Decision-making style and preferences

This is the **operating profile** for the agent. Agents read `USER.md` at the start of every session to understand whose decisions they are supporting.

**Current state:** Not enforced by the CLI. Vault operators typically maintain a root-level `<operator-slug>.md` file that serves this purpose.

---

### 3. MEMORY.md

Long-term agent memory.

This file captures:

- Recurring patterns the agent has observed
- Operator preferences learned over time
- Mistakes made and lessons learned
- Context that doesn't fit in any single note
- Agent-specific state that persists across sessions

This is the **agent's working memory** — what it remembers from past sessions that isn't in the vault's notes.

**Current state:** Not yet implemented. The current system is stateless across sessions (agents start fresh each time).

---

### 4. tekmen_memex

Curated human/strategic manifest.

This is the **operator's core identity note** — their strategic thesis, active philosophies, operating principles, and the high-level mental models that drive their decisions.

Unlike `USER.md` (operating profile), this is the **strategic anchor** — the beliefs and frameworks that define the operator as a thinker and operator.

Example: `tekmen_memex` contains Tekmen's thesis on programmable money, his conviction around infrastructure leverage, his execution principle, and his meta-method.

This is the **manifest** — the operator's curated self.

**Current state:** Vault operators typically maintain a root-level note (e.g., `tekmen_memex.md` or `<operator-slug>.md`) that serves this purpose. Not enforced by schema.

---

## Why a Quartet, Not a Single File?

The original design used a single `soul.md` to define everything. This collapsed four distinct concerns into one file:

1. **Agent behavior** (how to think, cite, retrieve)
2. **Operator profile** (who is being served, how they operate)
3. **Agent memory** (what the agent has learned over time)
4. **Operator manifest** (strategic thesis, core philosophies)

Separating these into four components makes each one **independently updatable**:

- Change the agent's voice without rewriting the operator's strategic thesis.
- Update agent memory without touching the operator's profile.
- Onboard a new operator without rewriting the agent's behavior.
- Evolve strategic beliefs without changing how the agent retrieves.

The quartet is **modular by design**.

---

## How Agents Use the Quartet

At the start of every session, an agent should:

1. Read `SOUL.md` — learn how to operate (voice, tone, red lines)
2. Read `USER.md` — learn the operator's profile (role, projects, preferences)
3. Read `MEMORY.md` — recall what was learned in past sessions
4. Read `tekmen_memex` — ground in the operator's strategic thesis and core beliefs

This four-step initialization grounds the agent in both **identity** (agent + operator) and **continuity** (memory + manifest).

---

## Current vs. Target State

| Component | Current state (0.2.0) | Target state (Mark 1) |
|-----------|----------------------|----------------------|
| `SOUL.md` | Template exists in `engineering/agent-soul.md` | Canonical file at vault root, enforced by MCP server |
| `USER.md` | Operator maintains a `<slug>.md` file by convention | Required root file, schema-validated |
| `MEMORY.md` | Not implemented (agents are stateless) | Canonical file at vault root, updated by agents after each session |
| `tekmen_memex` | Operator maintains a root-level note by convention | Required root file, schema-validated, curated human manifest |

The **engineering challenge** is not technical — it is governance. Consolidating the quartet requires deciding which pieces of current documentation become **canonical policy** (part of `MEMORY.md`) and which remain **guidance** (in the docs).

---

## Justified Absence: No Automatic Generation

The quartet is **not auto-generated** from the vault. Each file is **hand-written** (SOUL, USER, tekmen_memex) or **agent-maintained** (MEMORY).

Why?

- **SOUL, USER, tekmen_memex** define **intent** — they are stable, deliberate, operator-owned.
- **MEMORY** records **state** — it evolves with every session as the agent learns.

Auto-generating the manifest from vault statistics would produce a description of what happened to be captured recently, not a description of what the system is **for**.

---

[← Mark 1 Operating Core](../../16-mark1-operating-core.md) · [Engineering index](../README.md) · [Firewall →](firewall.md)
