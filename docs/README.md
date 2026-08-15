# MemexLab Engine — Documentation

**`0.2.0-harness-preview`** · Local-first · Markdown-native · Agent-operable

The full-stack documentation for **`memex`** — a Python CLI that operates a local-first,
markdown-native knowledge vault: it compiles raw sources into atomic notes, maintains a
linked canonical layer, runs deterministic retrieval and lint, and generates cited outputs.

> The filesystem is the database. Plain markdown is the storage. Obsidian is the editor.
> A Python CLI (`memex`) is the engine. No cloud. No lock-in.

**New:** The **[Memex Mark 1 Operating Core](16-mark1-operating-core.md)** documentation describes the conceptual architecture — a sovereign operating system (Graph + Evidence + Belief + Action + Governance) with nine layers, seven named agents, and a six-grade firewall. Mark 1 is the north star; the CLI docs below describe the current implementation.

## Start here

- **[MemexLab in One Page](00-one-page.md)** — the whole system at a glance.
- **[Quickstart](quickstart.md)** — the compressed setup path.
- **[Onboarding Guide](10-onboarding-guide.md)** — complete step-by-step setup.
- **[Overview](01-overview.md)** — what MemexLab is, and why.

## Core documentation

| # | Section | What it covers |
| --- | --- | --- |
| 1 | [Overview](01-overview.md) | What it is, the problem, the philosophy |
| 2 | [Architecture](02-architecture.md) | Vault + engine, layer-by-layer, information flow |
| 3 | [Core Concepts](03-core-concepts.md) | Sources, canonical notes, ontology, harness, resolvers |
| 4 | [Folder Structure](04-folder-structure.md) | Every folder and naming convention |
| 5 | [Daily Workflow](05-daily-workflow.md) | The eight-step flow, worked end-to-end |
| 6 | [Templates & Note Types](06-templates-and-note-types.md) | The template inventory and principles |
| 7 | [Metadata & Tagging](07-metadata-and-tagging-rules.md) | The three schemas, fields, tags, linking rules |
| 8 | [Automation & Scripts](08-automation-and-scripts.md) | The engine command-by-command; what it never does |
| 9 | [User Modes](09-user-modes.md) | Beginner, researcher, founder, operator, collaborator |
| 10 | [Onboarding Guide](10-onboarding-guide.md) | Zero to operating, step by step |
| 11 | [Best Practices](11-best-practices.md) | What to do |
| 12 | [Common Mistakes](12-common-mistakes-and-anti-patterns.md) | What to avoid |
| 13 | [Maintenance](13-maintenance.md) | Daily → yearly cadence, recovery |
| 14 | [Future Expansion](14-future-expansion.md) | Bounded ways the system may grow |
| 15 | [FAQ](15-faq.md) | Setup, practice, schema, edge cases, philosophy |

## Reference

- **[Quickstart](quickstart.md)** — ten-minute setup path.
- **[Vault Sync](vault-sync.md)** — sync the vault across devices with git: private remotes, mobile, conflicts, secrets.
- **[Capture Anywhere](capture-anywhere.md)** — one-gesture capture on every device: CLI, bookmarklet, iOS share-sheet Shortcut, Android.
- **[Maintenance Checklist](maintenance-checklist.md)** — checklists by cadence.
- **[Glossary](glossary.md)** — every term used in this documentation.

## Engineering & design

Deeper design references — architecture, harness, observability, governance, taxonomy,
benchmarks, roadmap, and credits — live under **[engineering/](engineering/README.md)**.

---

This is the engine's documentation. Generic placeholders (`<your-name>`, `<your-company>`,
`<your-product>`, `<your-vault>`) stand in for any personal data. Render it as a local docs
site with `mkdocs serve` (see [`mkdocs.yml`](../mkdocs.yml)).
