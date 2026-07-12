# MemexLab in One Page

What it is. A markdown-native governed memory layer for agents that turns reading, thinking, and daily capture into durable, queryable, linkable knowledge — with an LLM-powered engine that helps you compile sources into atomic notes and generate essays, decks, and answers from them.

What makes it different. The filesystem is the database. Plain markdown is the storage. Obsidian is the editor. A Python CLI (`memex`) is the engine. No cloud. No lock-in. Everything the engine does is deterministic except where an LLM is explicitly invoked, and those calls are dry-run by default, snapshotted before apply, and cite their sources by slug.

• • •

## The flow

```
  inbox/ → raw/ → wiki/ → projects/ → outputs (_qa, _essays, _slides, _index, _charts)     ↑                        ↑             ↑     └─────── feedback ───────┴─────────────┘
```

Capture into `inbox/` — fast, unstructured, no decisions. Promote to `raw/` during the weekly review — full text, citation metadata. Compile with `memex compile` — LLM reads raw, proposes atomic notes for `wiki/`. Link — every wiki note links to at least two others. Promote status: `seed` → `draft` → `evergreen` as notes earn trust. Produce on demand — `memex qa`, `memex export essay`, `memex export slides`. Feed back — every output surfaces gaps; you fill them; the vault compounds.

• • •

## The folders

```
<your-vault>/  <your-name>.md       persona core — always in LLM context  memexlab.md        system core — always in LLM context  inbox/                 fast capture  raw/                   sources with citation metadata  wiki/                  atomic canonical notes — your thinking  people/ companies/ philosophies/ eras/   ontology entities  projects/<slug>/       goal-driven workspaces with end dates  archive/               what no longer earns active space  templates/             Templater frontmatter  _qa/ _index/ _essays/ _slides/ _charts/ _lint/   engine outputs  .memex/                snapshots, log, state
```

• • •

## The engine

```
memex doctor    config sanity checkmemex migrate   bring frontmatter up to schema (dry-run + snapshot + apply)memex rollback  inverse of migrate --applymemex compile   raw source → atomic notes (LLM)memex lint      validate frontmatter, links, stubsmemex qa        answer a question with cited sources (LLM)memex index     reading order / concept map / problem view (LLM)memex export essay   topic → full essay (LLM)memex export slides  topic → Marp-compatible deck (LLM)memex chart     tag frequency / type distribution / latticework coverage / timeline
```

Universal contract. Dry-run by default; `--apply` to write; snapshots before any migration; one JSON event to stderr per invocation; exit `0` on success, `1` on error.

• • •

## The schema

Three frontmatter types, dispatched by folder:

- AtomicFrontmatter — wiki and engine outputs. Required: `date`, `type`, `status`, `tags`, `latticework`.

- CuratedFrontmatter — ontology, raw sources, projects. Required: `title`, `type`, `created`, `updated`, `status`, `tags`, `latticework`.

- CoreFrontmatter — two root files. Required: same as curated plus whitelisted `type` values (`persona | homepage | manifest`).

Atomic `type` values. `article | qa | lint | index | essay | slides | chart`. Statuses. `seed | draft | evergreen` (atomic); `seed | draft | active | evergreen` (curated). Latticework problems. `problem-1` (seeing reality) through `problem-5` (playing long games).

Unknown keys are rejected. Broken links are errors. Lint fails the run on any error finding.

• • •

## The rhythm

Cadence

Effort

What

Daily

automated

`scripts/lint_daily.py` writes a dated report; fix errors same-day

Weekly

60–90 min

Inbox sweep → raw triage → compile queue → link pass → lint review

Monthly

2–3 hr

Merge duplicates, promote drafts, refresh ontology, coverage charts

Quarterly

4–6 hr

One essay on a major topic; feedback gaps into the vault

Yearly

1 day

Full ontology audit; tag taxonomy review; schema wish list

• • •

## The non-negotiables

- Dry-run before `--apply`, always.

- Read every compile output before applying.

- Every atomic note carries provenance: `source:` or `cited_slugs:`.

- Status transitions are manual; no auto-promotion.

- Links into `archive/` from active notes are forbidden.

- API key in shell environment only; never in any file under version control.

• • •

## The domains this vault is tuned for

Programmable money · stablecoin settlement · AI-native banking · embedded finance · financial infrastructure · regulatory strategy (MiCA, CBDC frameworks, GCC) · <your-company> · <your-product> · Islamic finance compatibility.

The two core notes anchor every LLM call in these domains, which is why outputs sound like you, not like a generic PKM assistant.

• • •

## The compounding claim

Month 1: you have a working capture habit and a handful of atomic notes. Month 3: the vault can answer most questions in your primary domains. Month 6: first-draft outputs from the vault are better than first-draft outputs from scratch. Year 1: the vault is infrastructure for your thinking — a research assistant that never sleeps, never forgets, and never leaves.

The system is boring most days. It compounds.

---

[Docs index](README.md) · [Overview →](01-overview.md)
