
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

## Retrieval meter (shipped)

The run-level trace above is still a design target. What ships today is a narrower local log: one JSONL record per retrieval or answer, on disk, with no network call.

Paths that append a record: `mcp.get_index`, `mcp.search_vault`, `mcp.read_note`, `memex.search`, `memex.qa`.

```json
{"cited_slugs":["governed-memory"],"hit":null,"query":"governed memory","retrieved_tokens":12,"route":"mcp.search_vault","ts":"2026-11-06T00:00:00+00:00","v":1}
```

| Field | Meaning |
| --- | --- |
| `v` | Schema version. `1`. |
| `ts` | UTC timestamp. |
| `route` | Which path retrieved. |
| `retrieved_tokens` | `ceil(utf-8 bytes / 4)` of the text handed back. Search counts snippets. `read_note` counts the body. `get_index` counts the prompt index. `memex.qa` counts the context blocks placed in the prompt, not the answer. |
| `cited_slugs` | Slugs returned (retrieval) or `[[slug]]`s in the answer (`memex.qa`). |
| `hit` | `null` until a later local eval sets `true` or `false`. The writer never fills it. |
| `query` | Optional, one line, truncated to 200 characters. |

Default path: `<vault>/.memex/meter.jsonl`. Override with `MEMEX_METER_PATH` or `meter_path:` in the vault's `governance.yml`. `.memex/` is gitignored. An explicit path on `memex meter --path` wins over the env var, which wins over governance.

```bash
memex meter --vault ~/vault
python3 scripts/meter_summary.py --vault ~/vault --format json
```

`hit` / `miss` in the summary count records whose `hit` field is `true` / `false`. Nulls count as `pending`. A missing file is an empty summary.
