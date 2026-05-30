
# Harness Architecture

Memex is a harnessed memory operating system. The markdown vault is the source of truth, but reliability depends on the harness around the agent: where it runs, which tools it can use, what context it sees, how state survives, what gets traced, how results are verified, and which policies constrain action.

This document adapts the ETCLOVG taxonomy from Agent Harness Engineering: A Survey to the Memex stack.

Source: https://picrew.github.io/LLM-Harness/main.pdf

## ETCLOVG map

| Layer | Harness question | Memex implementation | Next hardening step |
| --- | --- | --- | --- |
| Execution | Where does the agent run and what bounds it? | Local workspace, Git, validation scripts, private repo boundary | Add sandbox profile documentation for local, CI, and cloud runs |
| Tool interface | Which capabilities are exposed and how are they described? | Agent Skills, scripts, GBrain/Mark1 CLI, GitHub remote | Add tool inventory with risk levels and owner notes |
| Context | What does the model see, retrieve, compact, or forget? | README, AGENTS-style rules, docs, daily memory, Brain markdown, GBrain index | Enforce context policy and state templates for long-running work |
| Lifecycle | How does work move from request to artifact? | Git commits, roadmap, templates, validation flow | Add task state files and handoff rules for multi-session work |
| Observability | What can we inspect after a run? | Git history, command outputs, validation logs, memory notes | Add JSONL trace records and run summaries |
| Verification | How do we know a run worked? | validate_index.py, validate_vault.py, eval rubric | Add readiness check and trajectory regression suite |
| Governance | What constrains action and publication? | Private repo, open-source checklist, governance docs | Add governance.yml and policy-sensitive approval gates |

## Design principles

1. Harness changes are system changes. A prompt, tool schema, context policy, validator, permission rule, or memory path can change agent behavior.
2. Context is a scarce resource. Retrieval quality is not enough; placement, compaction, and state preservation matter.
3. Observability and governance are first-class layers, not lifecycle footnotes.
4. Evaluation should score the trajectory, not only the final answer.
5. Durable state beats chat history for long-running work.

## Practical rule

Every meaningful Memex change should answer seven questions:

1. Execution: what environment did it assume?
2. Tools: which capabilities did it use?
3. Context: what evidence did it load and why?
4. Lifecycle: what state or artifact continues the work?
5. Observability: what trace or commit explains what happened?
6. Verification: what check passed?
7. Governance: what boundary or approval applied?
