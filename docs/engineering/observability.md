
# Observability

Observability is a first-class Memex layer. Git history explains file changes, but a harnessed memory system also needs run-level traces: what was retrieved, which tools were used, which policies mattered, what validation ran, and what failed.

Source: https://picrew.github.io/LLM-Harness/main.pdf

## Minimum trace schema

Use JSONL for append-only traces. One line should represent one agent run or meaningful sub-run.

~~~json
{
  "trace_id": "2026-05-28T18-45-00Z-example",
  "task_id": "memex-harness-preview",
  "actor": "agent-or-human",
  "session": "main",
  "model": "optional-model-name",
  "mode": "fast|standard|strict",
  "retrieved_sources": ["README.md", "docs/architecture.md"],
  "tools_called": ["validate_index", "validate_vault"],
  "files_changed": ["docs/harness-architecture.md"],
  "policy_version": "governance.yml",
  "tokens": null,
  "cost_usd": null,
  "latency_ms": null,
  "outcome": "passed|failed|partial",
  "failure_category": null,
  "validation": ["python3 scripts/validate_index.py"],
  "commit": null
}
~~~

## Failure categories

- model_reasoning
- tool_interface
- context_policy
- execution_environment
- lifecycle_orchestration
- evaluator
- governance
- external_dependency
- unclear_specification

## Operating rule

Final output is not enough. For important work, record the trajectory: retrieved sources, tool choices, files changed, validation run, governance decisions, and failure attribution.
