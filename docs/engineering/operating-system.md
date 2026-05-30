# Memex Operating System

Memex runs on a simple loop:

> Capture → Distill → Connect → Apply → Review

The harness layer adds one more operating loop around the knowledge loop:

> Prepare -> Execute -> Trace -> Verify -> Govern -> Learn

## 1. Capture

Capture promising raw material quickly, without over-processing.

Examples:

- book passages
- article excerpts
- meeting insights
- founder/investor/operator lessons
- market signals
- regulatory observations
- strategic questions

Capture belongs in `content/sources/`.

## 2. Distill

Turn sources into memex items.

A distilled item should answer:

- What is the core thesis?
- Why does it matter?
- What are the key ideas?
- What mental model does it strengthen or challenge?
- Where might this apply?
- What question should we keep asking?

Distillation belongs in `content/items/`.

## 3. Connect

Connect new ideas to existing themes.

Useful connection prompts:

- What does this remind us of?
- Which assumption does this challenge?
- What second-order consequence follows?
- Which decision could this improve?
- Which strategic theme does this reinforce?
- What would inversion say?

Future maps will live in `content/maps/`.

## 4. Apply

The system is only valuable if it improves judgment.

Apply notes to:

- strategy memos
- investment or product decisions
- regulatory positioning
- market expansion questions
- leadership and hiring principles
- personal learning plans

A note that never changes thinking is probably just storage.

## Harness operating modes

Every agent run trades off cost, quality, and speed. Use the lightest mode that is appropriate for the risk.

| Mode | Use when | Required behavior |
| --- | --- | --- |
| Fast | Read-only lookup or low-risk synthesis | Search, cite, answer, no durable writes unless requested |
| Standard | Normal ingest, docs, or repo edits | Retrieve, cite, update files, run relevant validation |
| Strict | Private data, public release, governance-sensitive work, or long-running automation | Run readiness checks, trace important actions, validate, preserve state, require human approval where policy says so |

Default to Standard for framework changes. Use Strict for public release, private-vault exposure, permission expansion, or external actions.

## 5. Review

Review periodically to compound the system.

Suggested cadence:

- **Weekly:** clean new captures and create distilled items.
- **Monthly:** merge repeated tags, update maps, identify emerging themes.
- **Quarterly:** ask which ideas changed decisions or deserved deletion.

## Quality bar

A memex item is ready when it contains at least one of:

- a clear thesis
- a reusable mental model
- a decision-relevant insight
- a high-quality question
- a cross-domain connection

If it has none of these, keep it as a source or discard it.
