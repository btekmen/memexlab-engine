
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

## Shipped capture contract

The code enforces a narrower rule than the design list above. `capture_note`
(MCP) and the runner's `write_file`:

- write only inside the vault's governed write dir (`write_dir:` in
  `governance.yml`, default `inbox/`)
- never overwrite or edit an existing note
- append the write to `.memexlab/log.jsonl`

`capture_note` accepts an optional `origin_ref`. The same value a second time
returns the existing note and does not change its bytes. Notes captured without
`origin_ref` are unchanged. There is no migration.

## Contested notes

`status` is optional. A note that does not have it keeps working, and no script
in this repo rewrites existing notes to add one.

When new evidence conflicts with a note, capture a **new** inbox note:

| Field | Meaning |
| --- | --- |
| `status` | `contested`. Also allowed on a new note, with no `contests` list: `active`, `stale`, `archived`. |
| `contests` | Slugs the new evidence disagrees with. Those files are read and then left byte-for-byte as they were. |
| body | The evidence. |
| `origin_ref` | Optional. The same value returns the contested note already filed. |

```bash
python3 scripts/resolve_contest.py capture --vault ~/vault \
  --title "Launch moved" --body "The review is now July 2026." \
  --contests sample-launch
python3 scripts/resolve_contest.py capture --vault ~/vault --apply \
  --title "Launch moved" --body "The review is now July 2026." \
  --contests sample-launch
```

The script is dry-run until `--apply`. `--apply` files a new note. It does not edit `sample-launch`.

`propose_resolution` (MCP) and `resolve_contest.py propose` file a second inbox note for a human to approve:

- `resolution: proposed`
- `resolves`: the contested slug
- `status: active` on the proposal note itself

The proposal states that filing it does not edit the contested note or the notes that note names. Applying the proposal is a human edit of the vault. The same `origin_ref` returns the proposal already filed.

`get_index` lists `status: contested` notes first. The line gains `contests [[slug]]` when that field is set, and `resolution: proposed` on a proposal. Search hits include `status` (empty when the note has none). A contested hit also includes `contests`.

Omit `status` and `contests` and `capture_note` behaves as before: the new note's status is the write-dir name (`inbox` unless `governance.yml` says otherwise).

`memex plasticity mws` and the MCP `plasticity` tool can recommend that an inbox note is worth promoting. The recommendation does not move or edit the file. See [Plasticity policies](plasticity.md).

Retrieval (`get_index`, `search_vault`, `read_note`, `memex search`, `memex qa`)
appends a local meter record under `.memex/meter.jsonl`. That file is not a note
and it is not uploaded. See [Observability](observability.md#retrieval-meter-shipped).
