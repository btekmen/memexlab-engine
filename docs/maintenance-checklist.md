# Maintenance Checklist

Literal checklists by cadence. Print these, stick them somewhere visible, tick them off. The longer-form reasoning for each item is in `12-maintenance.md`.

• • •

## Daily (2 minutes, with coffee)

- ☐ Open this morning’s `_lint/lint-YYYY-MM-DD.md` report.

- ☐ If there are error-severity findings: fix them before the workday starts.

- ☐ Skim `.memex/log.jsonl` for any `lint_daily_*_error` events; investigate if present.

Nothing else is required daily.

• • •

## Weekly (60–90 minutes, same day and time every week)

### Inbox sweep — 15–20 min

- ☐ Open `inbox/`.

- ☐ For every item: promote to `raw/` + delete inbox item, merge into an existing wiki note + delete inbox item, or delete outright.

- ☐ `inbox/` is empty at end of this step.

### Raw triage — 10–15 min

- ☐ For every new `raw/` file this week: add `processed: true/false` and, if false, `atomize: true/false` or equivalent annotation.

- ☐ No raw file is left in ambiguous state.

### Compile queue — 15–20 min

- ☐ For every raw file marked compile-now this week: `memex compile <path>` (dry-run).

- ☐ Review each dry-run against the source.

- ☐ `memex compile <path> --apply` for those whose plans are correct.

- ☐ Open each newly compiled wiki note; read it; edit weak prose.

### Link pass — 10–15 min

- ☐ Filter wiki for `status: seed` files created this week.

- ☐ Each has ≥ 2 outbound `[[links]]`.

- ☐ Create stub notes for any link targets that don’t yet exist.

### Lint report review — 5–10 min

- ☐ Open every `_lint/lint-*.md` report from the week.

- ☐ Error findings: zero remaining (fix now if any).

- ☐ Warning findings (orphans, duplicates): each investigated — link, merge, or note as future work.

- ☐ Info findings (stubs, missing latticework): two most interesting stubs scheduled for development.

### Close — 5 min

- ☐ `memex lint` exits clean.

- ☐ `git add . && git commit -m "weekly review YYYY-MM-DD"` in the vault repo (if versioned).

Gate. If lint is not clean and you have no more time, note the blocker somewhere visible; do not declare the review done.

• • •

## Monthly (2–3 hours, first working day of the month)

### Duplication sweep — 30 min

- ☐ `memex lint` — read all orphan warnings.

- ☐ For each orphan: decide link, merge, or archive.

- ☐ For merges: pick the stronger slug, copy content, find-and-replace inbound links, delete loser, run `memex lint` to confirm clean.

### Promotion pass — 30 min

- ☐ Wiki filter: `status: seed` older than 2 months.

- ☐ Each: promote to draft, merge, or archive.

- ☐ Wiki filter: `status: draft` older than 3 months and used in at least one output.

- ☐ Each: promote to evergreen (after re-validating claims) or leave as draft with reason.

### Ontology refresh — 30–45 min

- ☐ Walk every note in `people/`, `companies/`, `philosophies/`, `eras/`.

- ☐ Touch `updated:` field honestly.

- ☐ If entity’s status changed, update the body.

- ☐ Archive entities that are no longer active (`status: archived` + move to `archive/<subfolder>/`).

- ☐ New entities that emerged this month: create with full context now.

### Coverage check — 15 min

```
☐ memex chart latticework-coverage --apply.
☐ memex chart tag-frequency --top 20 --apply.
☐ memex chart type-distribution --apply.
```

- ☐ Open each chart. Identify one or two targeted actions based on gaps; add them as inbox items.

### Project close-outs — 15–30 min

- ☐ For every project with `target_end_date` past: promote generalisable notes to wiki; archive project folder.

### Backup — 5 min

- ☐ Off-device backup completed and verified (rsync / remote git push / Obsidian Sync up to date).

• • •

## Quarterly (4–6 hours, first weekend of the quarter)

### The essay pass

- ☐ Choose one major topic from your long-running themes.

```
☐ memex export essay "<topic framed as a position>" --apply.
```

- ☐ Read the first draft.

- ☐ Edit aggressively until it’s publication-quality.

- ☐ During editing, note every gap: missing concepts, weak claims, missing entities, missing links.

- ☐ After editing: create every stub the essay wanted to link to; fix every weak note; write every new atomic note the essay surfaced; promote every note that proved itself.

• • •

## Yearly (1 day, end of calendar year)

### Ontology audit — 3 hours

- ☐ Every `people/` note read.

- ☐ Every `companies/` note read.

- ☐ Every `philosophies/` note read.

- ☐ Every `eras/` note read.

- ☐ Each: `updated:` touched honestly; archive if no longer active; new context added if relevant.

### Tag taxonomy review — 1 hour

```
☐ memex chart tag-frequency --top 50.
```

- ☐ Tags used < 3 times: merge into a more general tag or kill.

- ☐ Near-duplicate tags: decide on canonical form; rename everywhere.

- ☐ Flat tags that should be namespaced: add prefix; rename.

### Schema review — 1 hour

- ☐ Read `memex/schemas.py` end to end.

- ☐ Note fields you wish existed.

- ☐ Note fields unused in the past year.

- ☐ Write next year’s schema wish list in `_essays/schema-wishlist-YYYY.md`.

### Archive cleanup — 1 hour

- ☐ Walk `archive/`.

- ☐ Confirm no active note links into `archive/` (linter enforces; double-check).

- ☐ Delete snapshots older than a year whose migrations are still valid.

### Infrastructure check — 1 hour

- ☐ Engine on latest stable version.

- ☐ All Obsidian plugins current.

- ☐ Python up to date.

- ☐ API key valid; no leaked copies in any repo.

- ☐ Backups running and restorable (do a test restore of one file).

### Year-in-review — 1 hour

```
☐ _essays/year-in-review-YYYY.md:
```

- ☐ What the vault accomplished this year.

- ☐ Where it failed you.

- ☐ What you’ll tend differently next year.

• • •

## Red-flag checklist (run if anything feels off)

Quick diagnostics when you suspect decay:

- ☐ Is `inbox/` empty? (If non-empty for > 1 week: decay.)

- ☐ Does `memex lint` exit clean? (If no: decay.)

- ☐ Did the daily cron run this morning? (`grep lint_daily_complete .memex/log.jsonl | tail -1`.)

- ☐ Has any new atomic note this week been used in an output? (If no for several weeks: output habit has lapsed.)

- ☐ Last weekly review completed on schedule? (If two missed in a row: the system is drifting.)

- ☐ Last monthly refactor done within the last five weeks? (If not: duplication is accumulating.)

- ☐ Backups ran in the last seven days? (If not: fix before anything else.)

Any one of these is a yellow flag. Two is red. Three means stop creating, start tending.

---

[← Quickstart](quickstart.md) · [Docs index](README.md) · [Glossary →](glossary.md)
