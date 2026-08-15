# Firewall & Data Classification

The **Memex Mark 1 Operating Core** firewall protects sensitive data using a six-grade classification system. Every note is assigned a grade. Every output respects it. Human review is required at every boundary crossing.

---

## The Six Grades

| Grade | Safe for | Example content | Default handling |
|-------|----------|----------------|------------------|
| **Personal private** | Vault only | Health records, family notes, personal journal | Never sent to external APIs without explicit override |
| **Company private internal** | Team members | Strategy memos, financial models, org charts, internal postmortems | Restricted to authenticated team context |
| **Investor-ready** | Fundraising context | Pitch decks, term sheets, cap tables, growth metrics | Approved for known investors and advisors |
| **Regulator-safe** | Compliance audit | Audited financial statements, regulatory filings, compliance documentation | Can be disclosed in regulatory review |
| **Public content** | Anyone | Blog posts, published papers, open-source docs, conference talks | Already public or approved for publication |
| **Group chat safe** | Low-stakes communication | Scheduling, logistics, public links, meeting reminders | OK for Slack, Discord, email |

---

## How Grades Are Assigned

### Manual Assignment (Current)

In the `0.2.0-harness-preview` CLI, grades are **not enforced**. Data classification is the operator's responsibility. Notes can carry a `visibility` field in frontmatter:

```yaml
visibility: private | shareable | public
```

This three-value system maps loosely to the six grades:

- `private` ≈ Personal private or Company private internal
- `shareable` ≈ Investor-ready or Regulator-safe
- `public` ≈ Public content or Group chat safe

The distinction is **coarse** and relies on operator judgment.

### Automatic Assignment (Under Development)

The **Disclosure Compiler** (not yet shipped) will assign grades automatically based on:

1. **Content analysis** — presence of names, financials, health data, credentials
2. **Provenance** — where the note came from (internal memo vs. public article)
3. **Entity links** — notes linking to `[[people/]]` or `[[companies/]]` entities inherit stricter grades
4. **Folder heuristics** — `raw/internal/` defaults to Company private internal; `_essays/` defaults to Public content

The compiler runs in **dry-run mode by default**. The operator reviews every proposed grade before applying.

---

## Boundary Crossing Rules

A **boundary crossing** happens when:

- A note classified as one grade is included in an output targeted at a lower-trust audience.
- An agent proposes sending Company private internal content to an external API.
- An essay draft pulls quotes from Personal private notes.

**Mark 1 policy:** Every boundary crossing requires **human approval**.

### Example: Essay Draft from Private Notes

```
Agent: Drafting essay on stablecoin settlement.
Retrieval: 12 notes, including [[internal/strategy-memo-q1]] (Company private internal).
Action: Flagging boundary crossing — essay will be Public content.
Decision: Human must either:
  1. Approve the specific quotes to be included (with redaction if needed), or
  2. Exclude the private note and regenerate the essay without it.
```

---

## Firewall Enforcement Layers

### 1. Provenance (Implemented)

Every note carries a `provenance` block listing sources and confidence. Agents are trained to cite sources and flag when they cannot.

### 2. Write Scopes (Partially Implemented)

The MCP server restricts agent writes to `inbox/`. Writes to other folders require explicit permission.

**Mark 1 extension:** Write scopes will respect grades — agents operating in "public content" mode cannot read Company private internal notes.

### 3. Egress Policy (Not Implemented)

An **egress policy** governs which notes can leave the vault:

- Personal private: Never sent to external APIs.
- Company private internal: Sent only to team-authenticated LLM endpoints.
- Public content: No restrictions.

**Current state:** No automatic enforcement. The operator is responsible for not pasting private notes into public contexts.

**Target state (Mark 1):** The engine checks every LLM call's context against the egress policy and blocks or warns on violations.

### 4. Disclosure Compiler (Not Implemented)

Scans the vault, proposes grades for every note, and surfaces conflicts (e.g., a Public content essay citing a Personal private source).

**When it ships,** the Disclosure Compiler will run as:

```bash
memex disclose --scan          # dry-run: show current grade coverage
memex disclose --check         # exit 1 if any boundary violations exist
memex disclose --propose       # propose grades for unclassified notes
memex disclose --apply         # apply proposed grades (with snapshot)
```

---

## Migration from Four Classes to Six Grades

The original governance model (documented in `engineering/governance.md` before this update) used **four classes**:

1. **Public** — safe to publish
2. **Internal** — restricted to team
3. **Confidential** — need-to-know only
4. **Sensitive** — no external APIs without approval

**Why six grades?**

The four-class model collapsed too many distinctions:

- "Confidential" bundled investor materials, board decks, and regulatory filings — but these have **different disclosure rules**.
- "Public" didn't distinguish between "already published" and "OK for group chat" — the latter is lower-stakes and doesn't need the same review rigor.
- "Sensitive" was too broad — health data, credentials, and financial models all need different handling.

The six-grade model separates these cases explicitly, reducing the need for judgment calls on every note.

---

## What Happens to Old Notes?

Notes written under the four-class model carry `visibility: private | shareable | public`. These are **still valid** but map to the new grades as follows:

| Old `visibility` | Suggested new grade |
|------------------|---------------------|
| `private` | **Company private internal** (default) or **Personal private** (if health/family) |
| `shareable` | **Investor-ready** (if fundraising) or **Regulator-safe** (if compliance) |
| `public` | **Public content** (if published) or **Group chat safe** (if informal) |

The **migration path**:

1. Run `memex disclose --scan` to see current coverage.
2. Run `memex disclose --propose` to get grade suggestions.
3. Review, edit, and apply.

No notes are auto-upgraded. The operator reviews every change.

---

## Human Review is the Final Gate

No automation substitutes for judgment. The firewall is a **forcing function** that surfaces decisions — it does not make them.

Every boundary crossing, every grade assignment, and every egress-policy override goes through a human. The system's job is to make those decisions **explicit, logged, and reviewable**, not to make them invisible.

---

[← Identity Quartet](identity-quartet.md) · [Engineering index](../README.md) · [Mark 1 Operating Core](../../16-mark1-operating-core.md)
