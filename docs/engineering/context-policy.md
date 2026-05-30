
# Context Policy

Context is scarce even when windows are large. Memex should treat context as an engineered state projection, not as a pile of text.

Source: https://picrew.github.io/LLM-Harness/main.pdf

## Policy

1. Preload only stable operating instructions and narrow task context.
2. Use progressive disclosure: keep paths, slugs, queries, and links available, then load details only when needed.
3. Prefer exact lookup before semantic recall when the entity or path is known.
4. Replace large tool outputs with durable artifact references after they have served their purpose.
5. Summaries must preserve decisions, constraints, unresolved issues, assumptions, provenance, and last verified timestamps.
6. Mark stale or uncertain claims explicitly. Do not let old summaries masquerade as current fact.
7. For long tasks, externalize state to a file using the state template before compaction, handoff, or pause.

## Three memory horizons

| Horizon | Use | Failure mode | Control |
| --- | --- | --- | --- |
| Active context | Immediate reasoning and tool use | Context rot, misplaced evidence, tool-output bloat | Progressive disclosure and tool-result clearing |
| Mid-term state | Multi-turn work, restarts, handoffs | Lost objectives, repeated work, stale assumptions | State files, daily memory, task notes |
| Long-term memory | Durable recall and synthesis | Bad provenance, outdated facts, retrieval drift | Brain/Memex markdown, GBrain indexes, contradiction handling |

## State-estimation rule

For any long-running task, the agent's internal state must be treated as a hypothesis about the real task state. The task state is reliable only when it is written to a durable artifact with enough evidence to reconstruct it.

A durable state artifact should include:

- current objective
- known facts
- assumptions
- open questions
- next actions
- stale or uncertain claims
- last verified timestamp
- relevant source paths or citations
