# Memex Operating System

Memex runs on a simple loop:

> Capture → Classify → Link → Pressure-test → Act → Learn

This is the complete operating loop for **Memex Mark 1 Operating Core**. Every iteration strengthens the system, tightening the relationship between what you capture and what you decide.

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

## 2. Classify

Turn sources into memex items with clear type and structure.

A classified item should answer:

- What is the core thesis?
- Why does it matter?
- What are the key ideas?
- What mental model does it strengthen or challenge?
- Where might this apply?
- What question should we keep asking?

Classification belongs in `content/items/` or the appropriate folder based on type.

## 3. Link

Connect new ideas to existing themes.

Useful connection prompts:

- What does this remind us of?
- Which assumption does this challenge?
- What second-order consequence follows?
- Which decision could this improve?
- Which strategic theme does this reinforce?
- What would inversion say?

Future maps will live in `content/maps/`.

## 4. Pressure-test

The system is only valuable if claims survive scrutiny.

Pressure-test notes by:

- Challenging assumptions with counter-evidence
- Running claims through the Skeptic agent
- Checking predictions against outcomes
- Comparing beliefs to reality
- Seeking disconfirming evidence

A claim that has never been tested is not yet knowledge.

## 5. Act

Apply notes to real decisions:

- strategy memos
- investment or product decisions
- regulatory positioning
- market expansion questions
- leadership and hiring principles
- personal learning plans

A note that never changes thinking is probably just storage.

## 6. Learn

Feed outcomes back into the system. When a decision resolves:

- Update the prediction ledger with actual outcomes
- Revise probabilities based on new evidence
- Archive beliefs that no longer hold
- Surface patterns that repeat

This closes the loop. What you learn becomes what you capture next.

## Harness operating modes

Every agent run trades off cost, quality, and speed. Use the lightest mode that is appropriate for the risk.

| Mode | Use when | Required behavior |
| --- | --- | --- |
| Fast | Read-only lookup or low-risk synthesis | Search, cite, answer, no durable writes unless requested |
| Standard | Normal ingest, docs, or repo edits | Retrieve, cite, update files, run relevant validation |
| Strict | Private data, public release, governance-sensitive work, or long-running automation | Run readiness checks, trace important actions, validate, preserve state, require human approval where policy says so |

Default to Standard for framework changes. Use Strict for public release, private-vault exposure, permission expansion, or external actions.

## Periodic Review

Review periodically to compound the system.

Suggested cadence:

- **Weekly:** clean new captures and classify items.
- **Monthly:** merge repeated tags, update maps, identify emerging themes, calibrate predictions.
- **Quarterly:** ask which ideas changed decisions or deserved deletion.

## Quality bar

A memex item is ready when it contains at least one of:

- a clear thesis
- a reusable mental model
- a decision-relevant insight
- a high-quality question
- a cross-domain connection

If it has none of these, keep it as a source or discard it.
