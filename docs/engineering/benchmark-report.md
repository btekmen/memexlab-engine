
# Benchmark Report

## Verdict

Memex is the canonical product repository. It absorbs the explanatory strength of the the executive guide prototype while keeping its own stronger technical substrate: schemas, skills, evals, synthetic examples, validation scripts, and CI.

## Compared repositories

| Repository | Role | Score |
| --- | --- | --- |
| memex | Canonical local-first, agent-operable second-brain framework | 8.1/10 |
| an executive-facing guide prototype | Executive-facing setup guide and GitHub Pages prototype | 6.8/10 |
| kepano/obsidian-skills | Obsidian-specific agent skill layer | Reference only |
| Andrej Karpathy's LLM Wiki | Primary upstream knowledge-base pattern | Lineage |
| garrytan/gstack | Skill-based agent operating system | Operational reference |
| garrytan/gbrain | Retrieval, graph, synthesis, and brain layer | Operational reference |

Primary credit belongs to Andrej Karpathy's LLM Knowledge Bases / LLM Wiki. Garry Tan's GStack and GBrain are the strongest operational references for turning the pattern into a repeatable agent system. See [Lineage and Credits](lineage.md).

## Memex vs the executive guide prototype

Memex wins on product credibility:

- Agent Skills-compatible workflows in skills/.
- Entity schema in schemas/entity.schema.json.
- Evaluation rubric and sample query set in evals/.
- Synthetic fake vault in examples/fake-vault/.
- Validation scripts and GitHub Actions.
- Real content and index pattern in content/.

The guide wins on explanation:

- Stronger from-scratch setup manual.
- Clearer governance and privacy framing.
- Better operator playbook.
- GitHub Pages landing page and styling.

Integration decision: copy the guide layer into Memex and make Memex the single canonical repo.

## Memex vs Obsidian Skills

kepano/obsidian-skills is a strong tool-use layer for Obsidian-flavored markdown. Memex should sit one level higher.

| Dimension | Obsidian Skills | Memex |
| --- | --- | --- |
| Primary job | Help agents edit Obsidian files correctly | Help agents reason over a citeable knowledge graph |
| Unit of work | Markdown syntax, bases, canvases, vault operations | Claims, entities, sources, relationships, decisions |
| Data model | Obsidian-native conventions | Typed entities with provenance and lifecycle |
| Retrieval | Not the central problem | Core architecture concern |
| Evaluation | Not primary | Built into repo through evals and rubrics |
| Privacy stance | General-purpose vault tooling | Explicit public framework and private vault boundary |

## What to borrow

- From the the executive guide prototype: setup clarity, governance language, operator cadence, Pages presentation.
- From Obsidian Skills: small focused skill files, editor-native discipline, practical command recipes.

## What to avoid

- Shipping only documentation without schemas, skills, examples, and tests.
- Staying at the markdown-helper layer without retrieval and citation quality.
- Using real private vault examples in a public framework repo.
- Measuring success by vibe rather than retrieval, citation, contradiction handling, and synthesis quality.

## Current evidence

Validation passes on the canonical repo:

- python3 scripts/validate_index.py
- python3 scripts/validate_vault.py examples/fake-vault

The framework now includes setup manual, architecture polish, governance guide, operator playbook, templates guide, GitHub Pages homepage, corrected roadmap, and benchmark report.

## Next benchmark step

Add an executable benchmark runner that reads evals/query-set.sample.yml, runs retrieval against a selected vault or index, and scores responses against evals/rubric.md.
