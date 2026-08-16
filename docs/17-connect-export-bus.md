# Connect / Export Bus

The **Memex Connect/Export bus** is the product layer that sits between you and the vault. It defines:

1. **Three Mac gestures** — the first-day UX (Save, Ask, Approve)
2. **iOS queue** — capture + approve only; no vault editing, no agents, no compilers
3. **One bus** — Connect in (inbox-only), Export out (graded, human-approved)
4. **Connector protocol** — one YAML + skill file per data source
5. **Export grades** — v1 ships three of the six-grade firewall

This page describes the **design target**. The Mac app, iOS client, connector files, and graded export are **not yet shipped**. Today's surface is the CLI (`memex-cli`) and MCP server (`memexlab-mcp`), which implement the underlying mechanics that the product gestures will orchestrate.

---

## Core Thesis

**Mac is the box. Phone is capture + approve. One vault. No web client. No middle API. No Zapier.**

- Your vault lives on your Mac (or in a synced folder — see [Vault Sync](vault-sync.md)).
- The phone captures to `inbox/` and approves queue items. It never edits the canonical wiki, never runs agents, never runs compilers.
- The Mac runs everything: agents, compilers, exports, approvals.
- No server in the middle. No cloud database. The filesystem is the database.

---

## Three Mac Gestures (First Day UX)

### 1. Save — ⌥+Space or Drop

**What it does:** File a new note into `inbox/` with provenance.

- Press **Option+Space** (customizable) to open a quick-capture dialog.
- Drag a file, PDF, email, or folder onto the app icon → automatically ingested into `inbox/`.
- Every capture carries frontmatter: `captured_via`, `source_url` (if available), timestamp.
- The canonical wiki (`wiki/`, `people/`, `companies/`, etc.) is **never written** by Save.

**Implementation today:** The CLI's `ingest` family (`ingest url`, `ingest kindle`, etc.) and the MCP server's `capture_note` tool. The gesture will orchestrate these, but they already exist and work.

### 2. Ask — Query the Vault

**What it does:** Deterministic search over the vault; answers cite `[[slug]]`.

- Ask a question in natural language.
- The engine searches with BM25 (or hybrid if semantic index exists), retrieves the top notes, and synthesizes an answer.
- Every claim in the answer cites a `[[slug]]` — no hallucination, no "the model says."
- **The frontier model is not silently called with your whole vault.** Retrieval is local; only the top-k results are sent to the LLM for synthesis.

**Implementation today:** The CLI's `search` and `qa` commands, and the MCP server's `search_vault` + `read_note` tools. The gesture will be a one-keystroke wrapper.

### 3. Approve — Review the Queue

**What it does:** Review pending actions; Apply / edit / drop.

- Agents propose actions (drafts, briefs, outreach messages, data edits).
- Every proposal lands in the queue as a task item with status `pending`.
- You review it: **Apply** (commit the result note and mark complete), **Edit** (modify and apply), or **Drop** (cancel).
- Agent writes are **untrusted until Apply**. The canonical vault stays untouched until you say yes.
- **Approve never sends outbound mail or posts.** It commits a note. Outbound actions are a separate Export decision.

**Implementation today:** The MCP server's `list_queue` and `complete_queue_item` tools. The gesture will be a review UI with Apply/Edit/Drop buttons.

---

## iOS Queue: Capture + Approve Only

The iOS client has **two jobs**:

1. **Capture** — Share sheet → `inbox/` (same as the Mac Save gesture).
2. **Approve** — Action/Approval notification: yes/no only.

**What the phone NEVER does:**

- Edit the canonical graph (`wiki/`, `people/`, `companies/`)
- Run compilers (Belief, Evidence, Disclosure)
- Run the seven agents (Archivist, Analyst, Skeptic, Decision, Relationship, Strategic Watch, Chief-of-Staff)
- Host a second OS or agent runtime
- Sync via a server API (the vault is synced via iCloud or Working Copy; see [Vault Sync](vault-sync.md))

**Why:** The phone is a capture device. The Mac is the engine. Splitting the runtime across two devices creates consistency nightmares, doubles the testing surface, and violates the local-first contract. If you need to run a compiler or agent, use the Mac — or wait until you're back at it.

---

## The Connect/Export Bus

### Connect (Inbound): Inbox-Only Write

**One door in:** `capture_note` (MCP) or `memex ingest` (CLI).

- Every write lands in `inbox/` with provenance frontmatter.
- Every write appends a JSON line to `.memexlab/log.jsonl` (audit log).
- The canonical vault (`wiki/`, `people/`, `companies/`, etc.) has **no modify path** from Connect. To edit a canonical note, you open it in Obsidian and edit it yourself, or you review a queue proposal and Apply it.

**MCP tool surface:**

| Tool | What it does |
|---|---|
| `capture_note` | File a new note into `inbox/` with provenance; append `.memexlab/log.jsonl` |
| `vault_info` | Vault overview: note count, sections, `write_dir` (always `"inbox"`), available views |
| `search_vault` | Deterministic BM25 search; results carry `slug`, `path`, `score`, `snippet` |
| `read_note` | Read one note by slug or relative path |
| `list_queue` | List task-queue items (pending by default) |
| `complete_queue_item` | Complete a queue task and file the result; canonical files stay untouched |

**Connector protocol:** A connector is **one file** (YAML frontmatter + skill body). It declares:

- Source name, category, and data shape (LinkedIn Complete export, Matter JSON, Audible XLSX)
- Ingest strategy: call `capture_note` for each item, or call CLI `ingest` commands
- Frontmatter schema: what fields to extract, how to tag, where to file

**First three connectors (not shipped, file-first, no OAuth yet):**

1. **LinkedIn archive** (Complete + Basic dumps)
2. **Matter export**
3. **Books** (Audible XLSX + Book Collection)

**Later (named, not first ship):** Amazon orders, bookmarks, WhatsApp account info, phone contacts, Learning.csv, then live OAuth for Gmail / Calendar / Slack / Readwise / Kindle / RSS.

### Export (Outbound): Graded, Human-Approved

**One door out:** Export commands (not yet shipped).

- Nothing leaves the vault without a **grade** and **human approval**.
- Grades replace the old four-class model with six levels (see [Firewall & Data Classification](engineering/mark-1/firewall.md)).
- **v1 ships three grades:**
  - **Private** (personal private)
  - **Internal** (company private internal)
  - **Public** (public content)
- **v2 grades (named, not shipped):** Investor-ready, Regulator-safe, Group chat safe.
- **Disclosure Compiler** (under development) will assign grades automatically, but the human picks the grade before anything leaves, and reviews every boundary crossing.

**What Export is not:**

- Not an API webhook.
- Not a Zapier integration.
- Not an automatic sync to a cloud service.

Export is a deliberate action: "Take this note (or these notes), assert that it carries this grade, and emit it as [essay markdown / slide deck / chart PNG / email draft / etc.]." The export command writes the artifact to disk. You decide what to do with it next.

---

## Dry-Run is the Engine Default

Every write command — `ingest`, `capture_note`, connector runs, export — is dry-run by default. Add `--apply` to commit.

This is the same contract as the rest of the CLI (see [Best Practices](11-best-practices.md)). The engine shows you what it will do, you review it, and then you tell it to do it. No silent writes. No "oops, I didn't mean to ingest 10,000 LinkedIn messages."

---

## Mapping Product Gestures to MCP Tools

| Product gesture | Underlying MCP tools | CLI equivalent |
|---|---|---|
| **Save** (Mac) | `capture_note` | `memex ingest <source>` |
| **Ask** (Mac) | `search_vault`, `read_note` | `memex search`, `memex qa` |
| **Approve** (Mac) | `list_queue`, `complete_queue_item` | (manual: read `queue/`, move result to canonical folder) |
| **Capture** (iOS) | `capture_note` | (share sheet writes to `inbox/` via sync) |
| **Approve** (iOS) | `complete_queue_item` (yes/no only) | (notification triggers the tool call on Mac) |

The MCP server is the **governed API** — it enforces inbox-only writes, provenance, and the audit log. The CLI commands are the **operator surface** — they call the same underlying logic. The product gestures (Mac app, iOS client) are the **first-day UX** — they orchestrate the tools so you don't have to remember the command syntax.

---

## What Is NOT Shipped

This page describes the **design target**, not the shipping state. Today (version `0.2.0-harness-preview`):

**Shipped:**

- `memex-cli` package: `ingest`, `view`, `search`, `qa`, `reindex`
- `memexlab-mcp` server: `vault_info`, `search_vault`, `read_note`, `capture_note`, `list_queue`, `complete_queue_item`
- Synthetic example vault (`examples/fake-vault`)
- Full MkDocs documentation

**Not shipped (design spec only):**

- Mac.app (Save / Ask / Approve gestures)
- iOS client (share sheet capture + notification approval)
- Connector files (LinkedIn, Matter, Books, etc.)
- Export commands (`memex export essay`, `memex export slides`, etc.)
- Disclosure Compiler (automatic grade assignment)
- Graded export enforcement

The mechanics are built. The product surface is next.

---

## Why This Matters

The Memex is not a note-taking app. It is a **governed memory system**. The Connect/Export bus is the enforcement boundary:

- **Connect in:** Everything that enters is logged, provenance-tagged, and filed into `inbox/`. No silent writes. No unattributed claims.
- **Export out:** Nothing leaves without a grade and human approval. No accidental leaks. No "I didn't know that was in the retrieval context."

The bus is the product lock. The six MCP tools are the API. The CLI is the operator surface. The Mac app and iOS client are the first-day UX. They all enforce the same contract: **local-first, citable, auditable, human-approved.**

---

[← Mark 1 Operating Core](16-mark1-operating-core.md) · [Docs index](README.md) · [Connecting Agents (MCP)](mcp-clients.md)
