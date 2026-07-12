# Memex Roadmap

## Phase 1 — Structured repository

Status: complete

- [x] Create repository structure
- [x] Import current local memex item
- [x] Add documentation
- [x] Add templates
- [x] Add lightweight validation script
- [x] Push to GitHub
- [x] Add synthetic example vault
- [x] Add schemas, skills, evals, and CI validation
- [x] Add GitHub Pages-ready docs layer

## Phase 2 — Capture discipline

- [x] Define standard capture workflow
- [x] Add source and entity templates
- [x] Add weekly review checklist
- [ ] Create `content/maps/` for cross-note synthesis
- [ ] Create first strategic map from existing AI deterrence note
- [ ] Add capture inbox path: `memex ingest url`, a bookmarklet, and a packaged mobile share-sheet recipe (dry-run first; browser extension deliberately deferred)
- [ ] Add highlight importers: `memex ingest kindle` / `memex ingest readwise` (deterministic parsers, idempotent re-import)
- [ ] Add feed ingestion: `memex ingest rss` / `memex ingest youtube-feed` (incremental state file, inbox-bound, volume-guarded)
- [ ] Add YouTube transcript ingestion with timestamp heading anchors (citable moments)
- [ ] Add git-based vault sync guide (private-remote setup, mobile paths, two-device walkthrough)

## Phase 3 — Retrieval and tooling

- [ ] Auto-rebuild `content/index.jsonl`
- [x] Validate YAML front matter for synthetic vault
- [ ] Normalize tags
- [ ] Add search script
- [ ] Add duplicate detection
- [ ] Add related-note suggestions
- [ ] Add benchmark runner for the sample query set
- [ ] Add saved views as files: named query notes usable from CLI and as an MCP search scope
- [ ] Add local reproducible semantic index (`memex reindex`, hybrid BM25+embedding retrieval, rebuildable cache; sequenced after the benchmark runner so the gain is measurable)

## Phase 4 — Strategic synthesis

- [ ] Build maps for recurring strategic themes
- [ ] Create decision-support templates
- [ ] Generate monthly synthesis reports
- [ ] Connect notes to projects and active questions
- [ ] Add summary preset lenses (key points, ELI5, translate, counter-case, action items) beside the frameworks lenses

## Phase 5 — Public readiness

- [x] Run final privacy scan. (docs privacy scrub, 2026-07)
- [ ] Audit git history before any public release.
- [ ] Expand fake vault with 10-20 synthetic entities.
- [ ] Add screenshots or diagrams for the Pages homepage.
- [ ] Publish GitHub Pages.
- [x] Add private-review version marker and changelog.
- [ ] Add public release notes and version tags.
- [ ] Publish `llms.txt` and raw-markdown mirrors of every docs page (agent-readable docs).
- [ ] Add an MCP client setup recipes page (Claude Code/Desktop, Cursor, and other MCP clients).
- [ ] Submit the MCP server to public registries/marketplaces (post-PyPI; readiness check + explicit approval per governance).

## Phase 6 — Harness preview

Status: active

- [x] Add ETCLOVG harness architecture.
- [x] Add context and memory policy.
- [x] Add observability and trace schema.
- [x] Add declarative governance policy.
- [x] Add state handoff template.
- [x] Add readiness check script.
- [x] Expand eval rubric with trajectory scoring.
- [ ] Add executable benchmark runner for trajectory evals.
- [ ] Add trace capture implementation.
- [ ] Add policy enforcement hooks.
- [ ] Add agent run history viewer.
- [ ] Add GBrain connector documentation.
- [ ] Add governed agent task queue: `queue/` directory with status-tracked markdown items, CLI transitions (dry-run first), and MCP v2 tools that require a filed result note before completion (after the MCP server launch and trace capture).
