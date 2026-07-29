# AGENTS.md — memexlab-engine

Adapter to the fleet-wide policy: [AI_OPERATING_SYSTEM.md](/Users/tekmen/_portfolio/AI_OPERATING_SYSTEM.md) (rules live there; repo facts live here).

## Purpose

MemexLab Engine — the governed memory layer for AI agents. Public (MIT) monorepo, `0.2.0-harness-preview`: agent-operable framework (skills, schemas, evals, governance, synthetic example vault), full MkDocs documentation, plus two installable Python packages:

- **`memex-cli/`** — `memex` CLI (package `memexlab-cli`): local-first ingest/index/search over a plain-markdown vault.
- **`memexlab-mcp/`** — MCP server (`memexlab-mcp`): governed, citable local memory (`search_vault` / `read_note` / `capture_note`) for Claude Code / Desktop / Cursor.
- **`runner/`** — self-hosted reference agent (provider-agnostic, dry-run by default).

## Stack

Python >= 3.10, `uv` (each package has its own `uv.lock` and `.venv`), hatchling builds, pytest (~17 test files across the two packages), MkDocs Material docs.

## Commands

| Command | Where | Status |
|---|---|---|
| `PYTHONPATH=src uv run --with pytest pytest tests/ -q` | `memex-cli/` | **verified** 2026-07-29 — 61 passed in ~1s |
| `PYTHONPATH=src uv run pytest tests/ -q` | `memexlab-mcp/` | **verified** 2026-07-29 — 39 passed in ~1s |
| `python3 scripts/validate_vault.py examples/fake-vault` | repo root | **verified** 2026-07-29 — OK |
| `python3 runner/agent.py --dry-run --vault examples/fake-vault` | repo root | **verified** 2026-07-29 — boots, lists tools |
| `mkdocs serve` (needs `pip install mkdocs-material`) | repo root | declared |

Quirks (2026-07-29, this machine): the venvs' editable-install `.pth` files are present and correct but not applied at interpreter startup, so `import memex_cli` / `import memexlab_mcp` fails without `PYTHONPATH=src` — keep the prefix. `memex-cli` does not declare pytest as a dev dependency, hence `--with pytest` there.

## CI / deploy / distribution

- **No CI runs the tests.** The only workflow is `.github/workflows/docs.yml` (MkDocs → GitHub Pages on push to `main`). Run both pytest suites locally before pushing.
- Distribution is `uvx --from "git+https://github.com/btekmen/memexlab-engine#subdirectory=<pkg>"` (no PyPI release yet). Pushing `main` therefore ships directly to anyone installing from git, and rebuilds the public docs site.

## Guardrails

- **SHARED REMOTE — verify your history before pushing.** A second, *unrelated* project (Colendi Ontology, `/Users/tekmen/Documents/Colendi Ontology`, root commit `fd3b9f5`) pushes branches to the SAME remote `btekmen/memexlab-engine`. This repo's root commit is `028e8e04`. Before any push: `git log --oneline | tail -1` and confirm you are on engine history, and never force-push or "clean up" branches you don't recognize.
- Local `main` was **behind `origin/main` by 10** (2026-07-29) — fetch/fast-forward before branching work you intend to push.
- **17 local topic branches (13 local-only, upstreams deleted) hold WIP** — do not prune or delete them.
- A second stale checkout of this repo exists at `/Users/tekmen/Desktop/memexlab-engine` — **this** copy is canonical (see registry.yaml).
- Public repo: no private data, no secrets, synthetic examples only — see [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
- Repo lives on Desktop (iCloud-synced): a hanging read/build may be APFS eviction, not a bug (`ls -lO <file>` shows `dataless`).

## Justified absences

- No root `ARCHITECTURE.md` — the architecture is fully documented in [docs/02-architecture.md](docs/02-architecture.md) and [docs/engineering/](docs/engineering/README.md).
- No `.env.example` — no `.env` convention; optional provider keys (`ANTHROPIC_API_KEY` / `OPENAI_API_KEY`) are read from the process environment only, and deterministic modes need no key.
