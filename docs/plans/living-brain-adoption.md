# Living Brain adoption plan

Local-only adoption of five ideas from the Living Brain comparison
([living-brain-vs-memex](https://github.com/btekmen/memexlab-engine)). Nothing in
this plan uploads a vault, calls a hosted memory API, or migrates existing notes.

The library stays the asset. The librarian stays the engineering. The model stays
replaceable.

## Status

- Items 1 and 5 are on `cursor/living-brain-local-adoption-2008`: `get_index`,
  idempotent inbox capture, and the local retrieval meter.
- Item 2 is the stacked follow-up: [`scripts/eval_arms.py`](../../scripts/eval_arms.py),
  documented in [Evals](../evals.md). The private Tekmen-eval question set stays
  outside the repository.
- Item 3 is the next stacked follow-up: `status: contested` on a new inbox note,
  and `propose_resolution` files a proposal a human approves. Existing notes are
  not rewritten.
- Item 4 is this stacked follow-up: open RPS and MWS weights in
  `plasticity.yml`, scored read-only. See [Plasticity policies](../engineering/plasticity.md).

## Constraints

- Local files only. No network calls on the capture, index, search, read, or meter paths.
- No schema migration. New frontmatter (`origin_ref`) appears only on notes captured
  with that argument. Existing notes are not rewritten.
- Agents still cannot edit or overwrite a note. A repeat capture returns the existing
  file or writes a new inbox file. It never opens an existing note for update.
- Items 6 (capture classifier) and 7 (health meters) in the source note are out of
  this five. Idempotent `origin_ref` from item 6 is pulled into item 1 because
  capture needs it. The classifier itself is not in scope.

## The five items

### 1. Cross-tool MCP memory endpoint — this PR

One stdio server, one vault, one contract for Cursor, Claude Code, and any other
MCP client. Extend `memexlab-mcp`; do not add a second server.

| Contract name | Shipped tool | Behavior |
| --- | --- | --- |
| prompt index | `get_index` | One line per note: `[[slug]]`, title, section, type, status. No bodies. |
| search | `search_vault` | Existing deterministic BM25. Unchanged name. |
| read | `read_note` | Existing read by slug or path. |
| capture | `capture_note` | Existing inbox write, plus optional `origin_ref`. |

`vault_info`, `list_queue`, and `complete_queue_item` stay as they are.

Effort: one package (`memexlab-mcp`), plus the docs that list the tools. The write
path gains a lookup and an optional frontmatter field. No new service, no vault
rewrite. Invasive only at the tool registry and `governance.capture_note`.

### 2. LoCoMo + Tekmen-eval — stacked follow-up

A public LoCoMo adapter under `scripts/` / `evals/` that scores retrieval with the
meter's token counts, plus a private Tekmen-eval set (reminders, decisions, company
facts) that never enters this repository.

Effort: a benchmark harness and an opt-in local dataset. No note-schema change.
Medium-high because scoring, the public/private split, and token accounting have to
land together. Depends on the meter format from item 5.

### 3. Contested notes + resolve — stacked follow-up

When new information conflicts with an existing claim, do not overwrite. Record
`status: contested` on a new note and resolve it with an explicit human step.

Effort: a status value the index already knows how to display, a resolve skill, and
tests that an agent cannot silently replace a canonical note. No migration of notes
that lack `status`. Medium. Depends on nothing structural; sequence it after the
MCP contract so clients already read `status` from `get_index`.

### 4. Local plasticity scores — stacked follow-up

Open, inspectable stand-ins for RPS and MWS. Weights live in YAML in the vault.
RPS is which notes should re-enter a morning brief. MWS is whether an inbox note
is worth a human promotion. Do not copy closed formulas. PFS and CRS are not
assigned formulas in this change.

Effort: a policy file and a read-only scorer. The factors use the meter from
item 5 and the contested status from item 3. Weights stay at the documented
defaults.

### 5. Token and citation metering — this PR

Every retrieval and answer path appends one JSONL record: retrieved token count,
cited slugs, and `hit: null` for a later eval. Default file:
`<vault>/.memex/meter.jsonl` (already gitignored via `.memex/`). Override with
`MEMEX_METER_PATH` or `meter_path:` in the vault's `governance.yml`. Summary:
`memex meter` and `python3 scripts/meter_summary.py`.

Paths that record: `mcp.get_index`, `mcp.search_vault`, `mcp.read_note`,
`memex.search`, `memex.qa`. Capture does not record; it is not a retrieval.

Effort: a small writer in each of the two packages (they do not share an import
path) and one stdlib summary script. No network, no note edits. Lands in this PR
so the new index and the existing search/read/qa paths are measured from the start.

## Order

1. **This PR** — plan, item 1, item 5. The contract and the measurement of that
   contract ship together.
2. **Item 2** — evals consume meter records. Tekmen-eval questions stay private.
3. **Item 3** — contested status on new notes; `get_index` already prints `status`
   when a note has one.
4. **Item 4** — plasticity YAML, RPS then MWS. Weights stay at the documented defaults.

## PR breakdown

| PR | Ships | Does not ship |
| --- | --- | --- |
| This one | Plan, `get_index`, idempotent `origin_ref` capture, local meter + summary | LoCoMo, contested workflow, plasticity weights, capture classifier |
| Stacked follow-up | LoCoMo adapter, three-arm harness, token columns from the meter, a documented slot for a private Tekmen-eval | The private question set itself |
| Stacked follow-up | `status: contested` on a new note, `propose_resolution`, contested lines in `get_index` and search | Rewriting existing notes, automatic silent merges, a migration that stamps status |
| Stacked follow-up | Open RPS and MWS weights in `plasticity.yml`, CLI and a read-only MCP tool, per-factor scores | Hosted scores, unpublished formulas, PFS/CRS formulas, automatic promotion |

## Deliberately not adopted

- Hosted Living Brain (`api.livingbrain.com`) or any upload of a private vault.
- Closed score formulas.
- Treating a LoCoMo marketing number as a Memex result. Item 2 measures this vault
  on this machine.
