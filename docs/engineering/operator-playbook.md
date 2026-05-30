
# Operator Playbook

## Daily

### Morning

```bash
python3 scripts/validate_index.py
python3 scripts/validate_vault.py examples/fake-vault
# Optional, for a connected private vault:
# gbrain sync --repo ~/private-vault --no-pull --no-embed
# gbrain embed --stale
# gbrain health
```

Review:

- today's calendar
- upcoming meetings
- inbox items
- open decisions
- stale follow-ups

### During the Day

For every important meeting:

1. create or update people pages
2. create meeting note
3. extract open threads
4. add follow-up actions
5. link companies and projects

### Evening

Process `inbox/`:

- promote durable facts into entity pages
- archive noise
- create decision records
- create or update project notes

## Weekly

Run validation and retrieval checks:

```bash
python3 scripts/validate_index.py
python3 scripts/validate_vault.py examples/fake-vault
# Optional private-vault checks:
# gbrain health
# gbrain query "what strategic risks changed this week?"
# gbrain query "which relationships need follow-up?"
# gbrain query "what decisions are waiting for evidence?"
```

Produce:

- weekly strategic review
- relationship follow-up list
- open decision register
- stale claim list

## Monthly

Run a maintenance review:

- duplicate entity scan
- dead links
- orphan pages
- outdated project pages
- unembedded chunks
- unsourced claims

## Executive Workflows

### Meeting Prep

Prompt:

```text
Prep me for the meeting with [person/company].
```

Expected output:

- who they are
- relationship history
- current relevance
- risks or sensitivities
- what to ask
- what not to say
- source slugs

### Relationship Map

Prompt:

```text
Who do we know at [company], ranked by relationship strength?
```

Expected output:

- top people
- roles
- last interaction
- best intro path
- confidence level

### Strategic Brief

Prompt:

```text
Brief me on [topic] using the brain, not generic web knowledge.
```

Expected output:

- answer first
- cited evidence
- inference clearly labeled
- recommended action

### Book Extraction

Prompt:

```text
Turn this book into mental models for our operating system.
```

Expected output:

- core thesis
- 5-10 mental models
- examples
- implications
- links to existing concepts

## Quality Bar

A good answer is:

- concise
- sourced
- current
- decision-relevant
- explicit about confidence
- clear about what is fact vs inference

A bad answer:

- sounds generic
- has no slugs
- invents relationship context
- ignores recent notes
- gives a balanced essay when a decision is needed
