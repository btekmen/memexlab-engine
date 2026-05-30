# Maintenance

Maintenance is how the vault survives time. A fresh vault is always clean; a two-year-old vault is clean only if someone has been tending to it. This page documents the tending — what to do, at what cadence, with what tools.

## Maintenance has layers

Cadence

Effort

Who does it

What it protects against

Daily

< 5 min

Automation (cron)

Schema drift, broken links

Weekly

60–90 min

Owner

Inbox rot, raw backlog, unlinked seeds

Monthly

2–3 hr

Owner

Duplicates, stale ontology, coverage imbalance

Quarterly

4–6 hr

Owner

Gaps in wiki coverage, unpromoted evergreens

Yearly

1 day

Owner

Stale entities, dead projects, ontology drift

The higher cadences (monthly/quarterly/yearly) cover what the lower cadences cannot. Skipping a layer transfers its work to the next one up — and each layer is more expensive than the one below it.

## Daily maintenance (automated)

The cron-scheduled `scripts/lint_daily.py` writes a dated report to `_lint/lint-YYYY-MM-DD.md` every morning. Your obligations:

- Glance at the lint report with coffee. Ten seconds.

- If there are error-severity findings, fix them today. Schema drift and broken links are not allowed to accumulate.

- If `.memex/log.jsonl` shows `lint_daily_*` failure events, investigate. Filesystem errors (`lint_daily_vault_error`) usually mean the vault path moved or a sync corrupted a file. Schema errors (`lint_daily_lint_error`) mean something was committed with invalid frontmatter.

No daily curation is expected. The daily layer is purely health-checking.

## Weekly maintenance (60–90 min)

Run this on a calendar block, same time every week. Coffee, no interruptions, door closed.

### 1. Inbox sweep (15–20 min)

Open `inbox/`. For each file, decide one of three outcomes:

- Promote to `raw/`. It’s a source you want to keep. Fetch full text, create the raw file, delete the inbox item.

- Merge into an atomic note. It’s a fact or quote that belongs in an existing wiki note. Paste it in with citation, delete the inbox item.

- Delete. It was capture enthusiasm that no longer earns its space. No ceremony; delete.

The inbox must be empty at the end of this step. Non-empty inbox is the single strongest predictor of vault decay.

### 2. Raw triage (10–15 min)

For each raw file created this week, decide:

- Compile now. The source is rich and you know what atomic notes you want from it.

- Compile later. The source is valuable but you need more time. Add `processed: false` frontmatter; leave it.

- Reference only. The source is worth keeping for quotation but doesn’t contain compilable material. Mark `processed: true, atomize: false`.

Never leave a raw file in ambiguous state. Ambiguity becomes backlog.

### 3. Compile queue (15–20 min)

Run `memex compile` on every file in the “compile now” bucket. Read each dry-run. Apply the ones whose plans look right. Open the newly-compiled wiki notes; read them; edit where the prose is weak or the claims are wrong.

If a compile produces notes you disagree with, don’t apply. Go back to the raw source, annotate further, and re-compile next week. The LLM will give you a different structure given a better-annotated source.

### 4. Link pass (10–15 min)

Open every `status: seed` note created this week. Ensure each has at least two outbound `[[links]]`. Create any stub notes needed for links that don’t yet resolve. Don’t develop the stubs now — the linter will surface them for later work.

### 5. Lint report review (5–10 min)

Open this week’s daily lint reports. For each one:

- Error findings — should already be zero by week’s end; if any remain, fix them now.

- Warning findings — orphans and duplicates. Investigate each; either link the orphan or merge the duplicate.

- Info findings — stub bodies, missing latticework fields. Pick the two most interesting stubs and develop them into real notes.

### 6. Close the loop (5 min)

Run `memex lint` one more time. If it’s clean, the week is done. If not, fix and re-run.

### Weekly checklist (copy-paste friendly)

- ☐ Inbox is empty.

- ☐ All new raw files have a `processed:` decision.

- ☐ All compiles for the week are reviewed and applied.

- ☐ All new `status: seed` notes have ≥2 outbound links.

- ☐ All lint errors from the week are resolved.

- ☐ `memex lint` exits clean.

## Monthly maintenance (2–3 hr)

The monthly block is refactoring. It turns accumulation into structure.

### 1. Duplication sweep (30 min)

Run `memex lint` with attention to orphan warnings. For each orphan atomic note, ask: is this a duplicate of a better-linked note? If yes, merge. Also run Obsidian’s graph view at “local graph, 2 hops” for each high-importance note; isolated satellite notes often turn out to be duplicates.

### 2. Promotion pass (30 min)

Filter wiki for `status: seed` notes older than two months. For each:

- Promote to draft if it’s earned it (see `10-best-practices.md` promotion criteria).

- Promote to evergreen if it’s also been used in an output and the claims are re-verified.

- Archive if it’s two months old, still seed, and has no inbound links — the vault has decided it doesn’t need the note.

Filter wiki for `status: draft` notes older than three months that have been used in at least one output. Candidates for evergreen; review and promote.

### 3. Ontology refresh (30–45 min)

Walk `people/`, `companies/`, `philosophies/`, `eras/`. For each entity note:

- Touch the `updated:` field honestly (only if you’ve re-read and it’s still accurate).

- If the entity’s status has changed (company pivoted, person moved, philosophy evolved), update the body accordingly.

- If the entity is no longer active or relevant, set `status: archived` and move to `archive/<folder>/` — but leave the link graph intact.

New entities that emerged during the month get their own notes now (not later).

### 4. Coverage check (15 min)

```
memex chart latticework-coverage --applymemex chart tag-frequency --top 20 --applymemex chart type-distribution --apply
```

Open the generated charts in Obsidian. Ask:

- Is the distribution across the five Latticework problems what you’d want? If Problem 5 (long games) has 4 notes and Problem 1 (seeing reality) has 200, you’re under-serving the long-range dimension.

- Are the top 20 tags the themes you actually care about? If the most frequent tag is `reaction/skeptical`, the vault is over-indexed on reactions and under-indexed on concepts.

- Is the type distribution healthy? A vault with 300 `article` notes and 3 `essay` notes suggests under-production.

Decide one or two targeted actions based on the gaps. Write them as inbox items so they’re picked up in next week’s sweep.

### 5. Project close-outs (15–30 min)

For any project whose `target_end_date` has passed:

- Promote every note in `projects/<slug>/notes/` that’s generalisable to the wiki.

- Archive the project folder: `archive/projects/<slug>/`.

- Update any entity notes that referenced the project’s status to reflect completion.

### 6. Backup (5 min)

Off-device backup. `rsync` to a remote host, push to a private git remote, or verify Obsidian Sync is current. If you can’t demonstrate that a backup was made this month, make one now.

### Monthly checklist

- ☐ Orphans investigated; duplicates merged.

- ☐ Promotion pass on seeds and drafts.

- ☐ Ontology `updated:` fields touched honestly.

- ☐ Charts generated and interpreted.

- ☐ Completed projects closed out.

- ☐ Off-device backup verified.

## Quarterly maintenance (4–6 hr)

The quarterly block is production. It exists because writing forces the vault to be complete in ways no other activity does.

### 1. Pick one major topic (5 min)

One of your long-running themes — “stablecoin settlement,” “embedded finance in Turkey,” “AI-native banking,” “Islamic finance compatibility for programmable money,” etc. Something you’ve been accumulating notes on for months.

### 2. Generate the essay (15 min)

```
memex export essay "<your chosen topic framed as a position>" --apply
```

Read the engine’s first draft.

### 3. Edit aggressively (2–3 hr)

This is the real work. The engine produces a structurally-sound first draft; editing turns it into something you’d publish. While editing, notice:

- Every `[[link]]` you had to remove because the target note was weak or wrong.

- Every claim you added from memory that isn’t in any vault note.

- Every concept the essay needed that doesn’t yet have its own atomic note.

- Every entity the essay referenced that doesn’t yet have its own entity note.

### 4. Feedback into the vault (1–2 hr)

Write every note the essay surfaced as a gap. Fix every weak note the essay exposed. Create every stub note the essay wanted to link to. Promote every note the essay successfully built on.

This step is the quarter’s largest single investment in vault quality. Don’t skip it. An essay written and then abandoned gives you the essay; an essay written and fed back gives you a better vault and the essay.

### Quarterly checklist

- ☐ One essay generated on a major topic.

- ☐ Essay edited to publication quality.

- ☐ All gaps surfaced by editing are filled in the vault.

## Yearly maintenance (1 day)

### 1. Ontology audit (3 hr)

Every entity note read. Every `updated:` field confronted. Every dead relationship archived. Every emergent entity created with its full context. The ontology is the vault’s skeleton; once a year, feel every bone.

### 2. Tag taxonomy review (1 hr)

Run `memex chart tag-frequency --top 50`. Look for:

- Tags used fewer than 3 times. Either merge into a more general tag, or kill.

- Tags with near-duplicates (`topic/stablecoin` vs `topic/stablecoins`). Decide on one; rename the other everywhere.

- Missing prefixes. A flat tag `#regulation` should be `topic/regulation`; update.

Tag renames are mass find-and-replace in Obsidian. Do them carefully.

### 3. Schema review (1 hr)

Read `memex/schemas.py`. Are there fields you’ve been wishing existed? Are there fields that haven’t been used in a year? This is the moment to plan schema changes for next year — not to execute them (that’s a separate, smaller project), just to identify them.

### 4. Archive cleanup (1 hr)

Walk `archive/`. Everything there should stay there — but confirm nothing in `archive/` is linked to from any active note. The linter enforces this, but a yearly manual check catches anything subtle.

### 5. Upgrade check (1 hr)

Is the engine on the latest stable version? Are all Obsidian plugins current? Is Python up-to-date? Is the API key still valid? Is the backup still running? A full green pass across all infrastructure means you can trust the vault for another year.

### 6. A short written reflection (1 hr)

Write a note, saved as `_essays/year-in-review-YYYY.md`, covering:

- What the vault accomplished this year.

- Where it failed you.

- What you’ll tend differently next year.

Keep it short. The point is the reflection, not the document.

### Yearly checklist

- ☐ Every entity note read and updated or archived.

- ☐ Tag taxonomy rationalised.

- ☐ Schema wish list written for next year.

- ☐ Archive verified (no active inbound links).

- ☐ Engine, plugins, Python, API key, backups all current.

- ☐ Year-in-review essay written.

## Archive rules

`archive/` exists so that deleting content is almost never necessary. Almost.

Move to archive, don’t delete, for:

- Ontology entities that are no longer active (a company you no longer track, a person no longer relevant to your work).

- Completed projects.

- Obsoleted wiki notes whose claims are wrong but whose history you want to preserve.

- Daily notes older than the retention window (if you use daily notes).

Delete, don’t archive, for:

- Inbox items that didn’t earn promotion.

- Captured text that turned out to be incorrect or unimportant.

- Outputs that were drafts only (never shared, never cited).

- Snapshots older than (for example) a year, after confirming the migrations they represent are still valid.

Never archive:

- Anything currently linked-to from active notes. Break the link first or promote the dependency.

- The two core notes. Their update history is the vault’s anchor.

## Versioning

The vault and the engine should both be version-controlled.

The vault. A private git repository. Commit weekly after the review. A year of weekly commits tells you, to the day, when a note was created, edited, or archived.

The engine. A git repository with semantic versioning. Every release has a changelog. Breaking changes are major-version bumps. Never run `git pull && deploy` on the engine without reading what changed.

Prompts are part of the engine. Prompt changes are tracked alongside code. A regression in output quality is diagnosed by `git log prompts/`.

## Recovery

Three recovery layers, in order of trust:

- `memex rollback` — for migration-caused damage. Replays a snapshot in reverse. Works only if a snapshot exists (which is always does, because `migrate --apply` always snapshots).

- Git history — for hand-caused damage. `git checkout <sha> -- <file>` restores any single file to any prior state.

- Off-device backup — for catastrophic damage (disk failure, ransomware, accidental full-directory deletion). `rsync` or the equivalent from the backup location.

If recovery from an off-device backup becomes necessary, treat the restored state as the new baseline. Verify schema, re-run lint, confirm no notes are missing before declaring recovery complete.

## Signs the system needs attention

- The inbox has been non-empty for more than a week.

- The daily lint report shows persistent error findings.

- You haven’t run `memex lint` in the past 48 hours.

- You’ve added 20+ new notes this week but haven’t used any in an output.

- You can’t find a note you know exists.

- An output cited a slug that no longer resolves.

- The monthly charts haven’t been generated in three months.

- You’ve skipped two weekly reviews in a row.

Any one of these is a yellow flag. Two simultaneously is a red flag. Fix what’s flagged before adding new content.

---

[← Common Mistakes and Anti-Patterns](12-common-mistakes-and-anti-patterns.md) · [Docs index](README.md) · [Future Expansion →](14-future-expansion.md)
