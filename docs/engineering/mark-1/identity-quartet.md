# Identity Quartet

The identity layer in **Memex Mark 1 Operating Core** is not a single file. It is a quartet of four components that together define who operates the system, how the system operates, and what the system remembers.

---

## The Four Components

### 1. SOUL.md

The operating mind — the system prompt that defines how agents think, retrieve, cite, and write.

This is the **personality** of the memory layer. It establishes:

- Voice and tone (dense, decisive, sourced)
- Citation discipline (`[[slug]]` syntax, no invented facts)
- Retrieval strategy (resolve before search, read before answer)
- Output contracts (briefs, not essays; answers, not explorations)

The soul is the agent's **identity**.

**Current state:** Implemented in `memexlab-mcp` as the base system prompt. See [Agent Soul](../agent-soul.md) for the template.

---

### 2. USER.md

The operator's identity and context — the person who owns the vault.

This file contains:

- Name, role, and primary organization
- Active projects and goals
- Strategic philosophies (the frameworks that shape decisions)
- Domain focus (industries, technologies, regulatory contexts)
- Contact preferences and communication style

This is the **grounding layer** for every LLM call. Agents read `USER.md` at the start of every session to understand whose memory they are operating.

**Current state:** Not enforced by the CLI. Vault operators typically maintain a root-level `<operator-slug>.md` file that serves this purpose.

---

### 3. MEMORY.md

The memory layer's structure and governance — the **rules of the vault**.

This file documents:

- Folder structure and schema
- Tag taxonomy
- Provenance rules (what sources are trusted, what confidence means)
- Write permissions (which agents can write where)
- Firewall grades and their boundaries

This is the **operating manual** for the memory layer itself.

**Current state:** Partially represented across multiple docs (`04-folder-structure.md`, `07-metadata-and-tagging-rules.md`, `engineering/governance.md`). Not yet consolidated into a single canonical `MEMORY.md`.

---

### 4. tekmen_memex (the vault slug)

The vault itself — the canonical name by which the memory layer is known.

In a multi-vault world (not yet implemented), each vault has a slug. In the single-operator case, the vault slug is the operator's memex identifier.

Example: `tekmen_memex`, `ahmet_brain`, `operator_vault`.

This is the **namespace** for the memory layer.

**Current state:** Implicit. The vault path is configured in the engine, but there is no first-class "vault slug" concept yet.

---

## Why a Quartet, Not a Single File?

The original design used a single `soul.md` to define everything. This collapsed three distinct concerns into one file:

1. **Agent behavior** (how to think, cite, retrieve)
2. **Operator identity** (who is being served, what they care about)
3. **System structure** (folder rules, schemas, governance)

Separating these into four components makes each one **independently updatable**:

- Change the agent's voice without rewriting the operator's bio.
- Update folder structure without touching the agent's retrieval strategy.
- Onboard a new operator without rewriting the system governance.

The quartet is **modular by design**.

---

## How Agents Use the Quartet

At the start of every session, an agent should:

1. Read `SOUL.md` — learn how to operate
2. Read `USER.md` — learn who they serve
3. Read `MEMORY.md` — learn the vault's structure
4. Confirm the vault slug matches expectations

This four-step initialization grounds the agent in both **identity** (who and how) and **structure** (what and where).

---

## Current vs. Target State

| Component | Current state (0.2.0) | Target state (Mark 1) |
|-----------|----------------------|----------------------|
| `SOUL.md` | Template exists in `engineering/agent-soul.md` | Canonical file at vault root, enforced by MCP server |
| `USER.md` | Operator maintains a `<slug>.md` file by convention | Required root file, schema-validated |
| `MEMORY.md` | Scattered across multiple docs | Consolidated canonical file at vault root |
| Vault slug | Implicit in vault path config | First-class identifier, used for multi-vault routing |

The **engineering challenge** is not technical — it is governance. Consolidating the quartet requires deciding which pieces of current documentation become **canonical policy** (part of `MEMORY.md`) and which remain **guidance** (in the docs).

---

## Justified Absence: No Automatic Generation

The quartet is **not auto-generated** from the vault. Each file is **hand-written** and **operator-owned**.

Why? Because the quartet defines **intent**, not **state**. The vault's current state is a messy, evolving corpus. The quartet is the **operating constitution** — it should be stable, deliberate, and rarely changed.

Auto-generating the quartet from vault statistics would produce a description of what happened to be captured recently, not a description of what the system is **for**.

---

[← Mark 1 Operating Core](../../16-mark1-operating-core.md) · [Engineering index](../README.md) · [Firewall →](firewall.md)
