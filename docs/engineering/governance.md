
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

### Public

Safe to publish:

- setup instructions
- generic architecture
- empty templates
- synthetic examples
- public-source summaries

### Internal

Restricted to team:

- operating playbooks
- project summaries
- non-sensitive decision logs
- sanitized strategy memos

### Confidential

Restricted to need-to-know:

- investor materials
- board materials
- legal documents
- financial models
- partner negotiations
- employee or candidate data

### Sensitive

Do not send to external LLM APIs without explicit approval:

- passwords
- access tokens
- personal IDs
- bank account data
- customer records
- medical or family information
- private communications

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
