
# Governance

## Operating Standard

Memex is a framework for institutional memory. Treat writes to real vaults as durable acts.

Rules:

- Search before answering.
- Cite before claiming.
- Add provenance before trusting.
- Preserve raw sources.
- Log durable writes.
- Never publish private vault content by accident.

## Data Classification

The **Memex Mark 1 Operating Core** uses a **six-grade classification system**. Every note is assigned a grade. Every output respects it. Human review is required at every boundary crossing.

### The Six Grades

| Grade | Safe for | Example content |
|-------|----------|----------------|
| **Personal private** | Vault only | Health records, family notes, personal journal |
| **Company private internal** | Team members | Strategy memos, financial models, org charts, internal postmortems |
| **Investor-ready** | Fundraising context | Pitch decks, term sheets, cap tables, growth metrics |
| **Regulator-safe** | Compliance audit | Audited financial statements, regulatory filings, compliance documentation |
| **Public content** | Anyone | Blog posts, published papers, open-source docs, conference talks |
| **Group chat safe** | Low-stakes communication | Scheduling, logistics, public links, meeting reminders |

### Why Six Grades?

The original four-class model (Public / Internal / Confidential / Sensitive) collapsed too many distinctions. Investor materials and regulatory filings have different disclosure rules. Published content and group-chat messages have different review requirements. The six-grade model separates these cases explicitly.

See [Firewall & Data Classification](mark-1/firewall.md) for the complete policy.

### Boundary Crossing Rules

A **boundary crossing** happens when a note classified as one grade is included in an output targeted at a lower-trust audience. Every boundary crossing requires **human approval**.

**Example:** An essay draft (Public content) citing an internal strategy memo (Company private internal) triggers a boundary-crossing review. The operator must either approve specific quotes with redaction or exclude the private note entirely.

## Provenance Rules

Every important claim should be traceable:

```yaml
provenance:
  - date: '2026-05-28'
    claim: 'The claim being made.'
    source: '[[sources/source-slug]]'
    confidence: high
```

Confidence levels:

- `high`: primary source or direct record
- `medium`: credible secondary source
- `low`: inference or weak source

## Write Rules

Agents may:

- create draft pages
- update working notes
- add provenance
- add backlinks
- generate briefs
- propose merges

Agents must not:

- rewrite raw sources
- delete pages without redirects
- publish externally without approval
- invent facts
- silently overwrite human edits
- commit secrets

## Review Rules

Use Git for review:

```bash
git status
git diff
git add .
git commit -m "Update brain notes"
```

For team environments:

- use pull requests
- protect main branch
- require review for schema changes
- allow agent-generated branches

## External Sharing

Before sharing anything outside the team:

1. confirm no private entity pages are included
2. scan for secrets
3. remove raw transcripts
4. replace real examples with synthetic ones
5. publish only the framework repo, never an unsanitized private vault

Basic scan:

```bash
rg -i "api[_-]?key|secret|password|token|private|confidential|sk-" .
```

No automated scan replaces judgment.
