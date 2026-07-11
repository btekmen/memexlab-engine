# MemexLab Engine

**`0.2.0-harness-preview`** · Local-first · Citable · Auditable

## The governed memory layer for AI agents.

*Local-first, citable, auditable. The model is swappable — the harness is the product.*

`memex` is a Python CLI that operates a local-first, markdown-native knowledge vault
for agents: it compiles raw sources into atomic notes, maintains a linked canonical
layer, runs deterministic retrieval and lint, and generates cited outputs — with
schema-governed artifacts, eval loops, and a public/private boundary a human reviews.

> The filesystem is the database. Plain markdown is the storage. A Python CLI (`memex`)
> is the engine. No cloud. No lock-in. The harness — not the model — is the product.

> **Memex** — the sovereign chief-of-staff app — is built on this engine.
> See [memex.memexlab.xyz](https://memex.memexlab.xyz).

## ⏱ Give your agent memory in 10 minutes

`memexlab-mcp` is a tiny MCP server that gives Claude Code, Claude Desktop, or Cursor
governed, citable, local memory over any folder of markdown:

```bash
claude mcp add memexlab -- uvx memexlab-mcp --vault ~/vault
```

*(PyPI release pending — until then use the git install in the [package README](memexlab-mcp/README.md).)*

Your agent can now `search_vault` (deterministic, citable `[[slug]]`s), `read_note`,
and `capture_note` — new notes land **only** in `inbox/` with provenance frontmatter,
every write is logged, and the canonical layer cannot be modified. Memory it can use;
memory it cannot corrupt. → [memexlab-mcp/README.md](memexlab-mcp/README.md)

![memexlab-mcp demo](docs/assets/memexlab-mcp-demo.gif)

> **`0.2.0-harness-preview` — early preview, not production-stable.** The agent-operable
> framework (skills, schemas, evals, governance, a synthetic example vault) lives here
> alongside the full documentation. The `memex` CLI package (the `compile`/`qa`/`lint`/`export`
> commands described in the docs) is maintained separately.

**Provider-agnostic.** The LLM integration is isolated in a single client, so you can point
the engine at any provider — Anthropic, OpenAI, or others (set `ANTHROPIC_API_KEY` or
`OPENAI_API_KEY`). The deterministic modes — lint, chart, retrieval, migrate — use no model
at all.

## What's in this repo

- **[`docs/`](docs/README.md)** — the full-stack documentation (indexed below).
- **`skills/`** — eight Agent Skills: `memex-ingest`, `memex-extract`, `memex-markdown`, `memex-query`, `memex-brief`, `memex-evaluate`, `memex-frameworks`, `memex-progress`.
- **`frameworks/`** — a library of mental-model lenses (first-principles, inversion, second-order effects, base rates, incentives) + the five-problem latticework.
- **`schemas/`** — `entity.schema.json`, the entity frontmatter schema.
- **`evals/`** — a sample query set (`query-set.sample.yml`) and a quality `rubric.md`.
- **`templates/`** — note templates (`item`, `source`, `state`).
- **`governance.yml`** — write/publish policy and the public/private vault boundary.
- **`examples/fake-vault/`** — a synthetic vault for demos and validation.
- **`examples/worked-example/`** — a complete pass (ingest → extract → frameworks → progress) over real public sources ([walkthrough](examples/worked-example/README.md)).
- **`library/`** — a growing collection of knowledge assets (papers, reports & books); `scripts/build_library_index.py` rebuilds [`library/README.md`](library/README.md).
- **`runner/`** — a self-hosted **reference agent**: a minimal local loop that operates a vault using the `skills/`, with a provider-agnostic backend (local model *or* hosted API, one env var). Try it with no key: `python3 runner/agent.py --dry-run --vault examples/fake-vault`. See [`runner/README.md`](runner/README.md).
- **`scripts/validate_vault.py`** — validate any vault, e.g. `python3 scripts/validate_vault.py examples/fake-vault`.

## Use with OpenClaw

The skills in `skills/` are designed for an [OpenClaw](https://github.com/openclaw/openclaw)
agent (MIT; Node 24 recommended, 22.19+ supported). Install the runtime from its official
source — we don't bundle it — then point it at this repo's `skills/`:

```bash
npm install -g openclaw@latest      # or: pnpm add -g openclaw@latest
openclaw onboard --install-daemon
```

See the [OpenClaw repo](https://github.com/openclaw/openclaw) for current install steps and
version support. The vault, schemas, and validation are runtime-agnostic — OpenClaw is the
default agent surface, not a hard requirement.

**Pairs with [`kepano/obsidian-skills`](https://github.com/kepano/obsidian-skills)** (MIT).
Both follow the Agent Skills spec, so they install side by side: obsidian-skills handle the
vault/file layer (markdown, bases, canvas, CLI, `defuddle` web extraction), MemexLab handles
the knowledge layer. See [Obsidian Skills: comparison & interop](docs/engineering/obsidian-skills-comparison.md).

## Start here

- **[MemexLab in One Page](docs/00-one-page.md)** — the whole system at a glance.
- **[Quickstart](docs/quickstart.md)** — the compressed setup path.
- **[Onboarding Guide](docs/10-onboarding-guide.md)** — complete step-by-step setup.
- **[Overview](docs/01-overview.md)** — what MemexLab is, and why.

## Documentation

| # | Section | What it covers |
| --- | --- | --- |
| 1 | [Overview](docs/01-overview.md) | What it is, the problem, the philosophy |
| 2 | [Architecture](docs/02-architecture.md) | Vault + engine, layer-by-layer, information flow |
| 3 | [Core Concepts](docs/03-core-concepts.md) | Sources, canonical notes, ontology, harness, resolvers |
| 4 | [Folder Structure](docs/04-folder-structure.md) | Every folder and naming convention |
| 5 | [Daily Workflow](docs/05-daily-workflow.md) | The eight-step flow, worked end-to-end |
| 6 | [Templates & Note Types](docs/06-templates-and-note-types.md) | The template inventory and principles |
| 7 | [Metadata & Tagging](docs/07-metadata-and-tagging-rules.md) | The three schemas, fields, tags, linking rules |
| 8 | [Automation & Scripts](docs/08-automation-and-scripts.md) | The engine command-by-command; what it never does |
| 9 | [User Modes](docs/09-user-modes.md) | Beginner, researcher, founder, operator, collaborator |
| 10 | [Onboarding Guide](docs/10-onboarding-guide.md) | Zero to operating, step by step |
| 11 | [Best Practices](docs/11-best-practices.md) | What to do |
| 12 | [Common Mistakes](docs/12-common-mistakes-and-anti-patterns.md) | What to avoid |
| 13 | [Maintenance](docs/13-maintenance.md) | Daily → yearly cadence, recovery |
| 14 | [Future Expansion](docs/14-future-expansion.md) | Bounded ways the system may grow |
| 15 | [FAQ](docs/15-faq.md) | Setup, practice, schema, edge cases, philosophy |

**Reference:** [Quickstart](docs/quickstart.md) · [Maintenance Checklist](docs/maintenance-checklist.md) · [Glossary](docs/glossary.md)

**Engineering & design:** [architecture · harness · observability · governance · taxonomy · benchmarks · roadmap · lineage](docs/engineering/README.md)

Render it as a local docs site:

```bash
pip install mkdocs-material
mkdocs serve   # then open http://127.0.0.1:8000
```

Generic placeholders (`<your-name>`, `<your-company>`, `<your-product>`, `<your-vault>`)
stand in for any personal data.

## Repository map

| Name | What it is | Visibility |
| --- | --- | --- |
| **`memexlab-engine`** (this repo) | The agent-operable engine framework + full documentation | Public |
| **`memexlab`** | The website ([memexlab.xyz](https://memexlab.xyz)) | Public |
| **`memexlab-docs`** | Documentation subset | Public |
| Personal vaults | Your actual knowledge base | Never published |

## License

[MIT](LICENSE).
