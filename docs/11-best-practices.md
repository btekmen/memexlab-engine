# Best Practices

Best practices for this system are not “keep your notes tidy.” They are the operating disciplines that make a governed, citable knowledge system compound instead of decay. Decay is the default state of any information system; compounding requires specific, repeatable habits. This page enumerates the ones that matter.

## Cleanliness

A clean vault is a vault where every file has earned its place and every frontmatter field is honest. Cleanliness is not aesthetic; it is the precondition for retrieval.

Lint at least daily. The scheduled `scripts/lint_daily.py` is non-optional. A vault that hasn’t been linted in a week is a vault where retrieval is already degraded by broken links and schema drift.

Resolve lint errors within 24 hours. An error-severity lint finding is a broken contract — either frontmatter doesn’t validate, or a wiki-link points to a missing note. Neither is tolerable overnight. Warnings and infos can wait for the weekly review.

Touch the `updated` field on curated notes honestly. Changing `updated:` signals “I looked at this today and it’s still right.” Updating it without reading the note is a form of lying to your future self. Conversely, an ontology note with a year-old `updated:` date is a yellow flag — either the entity matters and the note is stale, or the entity no longer matters and the note should move to `archive/`.

Do not let file-count grow faster than read-count. If you are creating five atomic notes a week but rereading fewer than five notes a week, the vault is an output device, not a thinking tool. Rebalance.

## Duplication prevention

Duplicates are the most common decay mode. `stablecoin-float-mechanics` and `pre-funded-stablecoin-float` are the same concept under two names. Both get linked; neither is canonical; the graph rots.

Before creating a new atomic note, search for it. Obsidian’s `Ctrl/Cmd-O` quick switcher and `Ctrl/Cmd-Shift-F` global search are both fast. Ten seconds of searching prevents an hour of eventual merging.

Prefer the more general title. `deferred-net-settlement` beats `deferred-net-settlement-in-stablecoin-contexts`. If the specific context deserves its own note, create it as a child and link upward.

Merge aggressively when found. When the weekly review surfaces a duplicate, merge immediately. Pick the stronger slug; copy content; update all inbound links; leave a redirect stub for the weaker note. Do not delete outright — the redirect stub preserves link resolution. See `06-templates-and-note-types.md`, "Redirect stubs", for the redirect frontmatter pattern.

Leave redirect stubs after merge. A merged entity becomes `type: redirect` with `aliasOf` pointing to the canonical slug. This lets the indexer resolve `[[old-slug]]` links to the winner, and external consumers can follow the redirect chain. The redirect body should state: `This entity was merged into [[canonical-slug]].` Human review is required before any merge.

Use the linter’s orphan warnings as a duplication signal. An orphan atomic note — one with zero inbound links — is often a duplicate in disguise. Investigate each orphan; either link it or merge-and-delete.

## Strong links

The graph is the skeleton of the governed memory layer. Weak links produce a weak graph; a weak graph produces weak retrieval.

Every atomic note should have at least two outbound links. One is often filler. Two forces you to articulate what the note is about in relation to its neighbours, which is the whole point of atomic notes.

Link by slug, not by display name. `[[deferred-net-settlement]]` is stable across title renames. `[[Deferred Net Settlement]]` breaks the moment you decide the canonical title should be lowercase.

Link to canonical concepts only. If you find yourself wanting to link to a note that feels like a tag — “all the things I think about Y” — that’s a sign the link should be a tag and the target should not exist as an atomic note at all.

Don’t link to placeholders unless you create the stub. A `[[gross-settlement]]` link to a nonexistent file is a broken link. Either create `gross-settlement.md` as a two-sentence stub (the linter will surface it for development) or rewrite the prose to not need the link.

## Promotion criteria

`status` is the most subjective field in the schema, and the most valuable when used honestly.

### When to promote seed → draft

- You’ve re-read the note at least once since creation.

- The body is coherent as prose, not a list of notes-to-self.

- Outbound links all exist and go somewhere real.

- The note’s claims are attributable — either to the `source:` raw file or to clearly-named external references in the body.

### When to promote draft → evergreen

- At least three weeks have passed since creation.

- You’ve used the note in at least one output (essay, QA answer, index).

- You’ve re-validated the claims against at least one newer source since creation.

- You’d stake a small reputational bet on the note’s claims being still true in five years.

### When to demote

Demotion is rare but legitimate. If an evergreen note is contradicted by new evidence, demote to `draft`, add a dated correction paragraph, and re-link where necessary. A vault that never demotes is a vault that isn’t watching itself.

## Review cadence

The cadence is hierarchical. Each level handles what the level below it cannot.

Daily (automated). The scheduled lint runs at 6 a.m. You glance at the report with coffee. Errors get fixed same-day.

Weekly (60–90 minutes). Inbox sweep → raw triage → compile queue → link pass → lint report review. See `09-onboarding.md` step 11 for the detailed procedure. This block is non-negotiable; without it, the inbox rots, which rots the rest of the system.

Monthly (2–3 hours). Refactor. Merge duplicates. Promote candidates. Update entity notes with the month’s new context. Run `memex chart latticework-coverage` and `memex chart tag-frequency` to inspect the vault’s shape; act on what the shape tells you. See `12-maintenance.md` for the monthly checklist.

Quarterly (4–6 hours). Write an essay on one major topic using `memex export essay`. The purpose is not the essay; it’s the feedback. Essay generation exposes every gap, duplicate, weak claim, and missing entity in the vault’s coverage of that topic.

Yearly (a day). Walk the ontology. Every `people/`, `companies/`, `philosophies/`, `eras/` note gets re-read. Stale relationships get archived. Ongoing relationships get their `updated` field touched honestly. New entities that emerged over the year get their own notes.

## Input quality

The vault can only be as good as its raw material.

Capture aggressively; ingest selectively. Anything into the inbox; only valuable sources into `raw/`. A capture that sits in the inbox for three weeks and never earns promotion gets deleted with no ceremony.

Prefer primary sources. A BIS working paper beats a blog post summarising it. A regulator’s own consultation document beats an industry newsletter’s take. For the domains this vault covers — stablecoin settlement, Islamic finance, CBDCs, regulatory strategy — primary sources disproportionately outperform secondary ones for durability.

Annotate while reading, not after. A raw file annotated the moment you finish reading carries the highest signal. A raw file annotated three weeks later carries roughly the same signal as the original article — which means the annotation step was noise.

Match raw depth to expected reuse. A source you’ll cite once in a blog post needs only the key quotes captured. A source you’ll cite a hundred times over five years — a foundational BIS paper, a milestone MiCA document — deserves full extraction with per-section notes.

## Output quality

Outputs are how the vault repays the investment. Treat them accordingly.

Every output is a first draft, not a final one. The engine’s essays, decks, and answers are starting structures. Edit them as you would edit any first draft — aggressively.

Cite by `[[slug]]` in every output, always. If you write an output and lose the slug citations during editing, you lose the chain back to the evidence. This is the single most common regression in practice; guard against it.

Produce weekly, even when you don’t need to. The discipline of producing — even a short QA answer to a question you already know the answer to — exercises the retrieval layer and surfaces graph weaknesses. A vault that only produces on demand produces worse when demand arrives.

File outputs back into the vault’s logic. Outputs live under `_essays/`, `_slides/`, `_qa/`, `_index/`, `_charts/`. They are first-class vault content and should be findable months later. An output saved to the desktop and forgotten is waste.

## LLM discipline

The LLM is a force multiplier and a drift vector. Good practice keeps the multiplier and minimises the drift.

Dry-run before `--apply`, always. See `07-automation.md`, Rule 1. This is the single most-violated rule in practice. Don’t.

Read every compile output before committing. A compile that adds four atomic notes you never read is four notes that will silently distort every future retrieval.

Keep prompts version-controlled. Every change in a prompt file is a change in engine behaviour. Review prompt diffs the way you’d review code diffs.

Use `--limit` to constrain cost and focus. `memex index` and the exporters default to generous token budgets. For narrow topics, `--limit 40` produces a more focused output than `--limit 100`.

Don’t chain LLM calls manually. If a task feels like it wants two or three LLM calls in sequence, don’t orchestrate that by hand — that’s a bug report for a future engine mode. See `07-automation.md`, Rule 6.

## Privacy and security

Treat the vault as personally sensitive. It contains your thinking, your positions, your unpublished research. The blast radius of a leaked vault is larger than the blast radius of a leaked inbox.

API key in the shell environment only. Not in `.env`, not in any file under version control. If you accidentally commit one, rotate immediately at your provider’s console.

Back up off-device at least weekly. Obsidian Sync, `tar cz` to a remote host, or a git push to a private remote. Disk failures are rare; the week you skip a backup is the week the drive fails.

Encrypt the repository at rest on mobile devices. If you sync the vault to an iPad or phone, ensure the device has full-disk encryption on, and consider whether truly sensitive positions should live in a separate vault subtree with stricter access.

## Longevity

The vault is infrastructure for decades. Short-term convenience that hurts long-term durability is the wrong trade.

Prefer plain markdown over Obsidian-specific syntax. Obsidian’s callouts, Dataview queries, and custom tags are useful but lock the content to Obsidian. Keep them to the minority of the vault’s content; keep the canonical atomic notes as portable markdown.

Don’t upgrade the engine without reading the changelog. A breaking change in the engine can silently invalidate months of notes. Read the changelog; run `memex doctor` after every upgrade; revert if anything is off.

Write for your future self, not your current self. Your current self has the context of the last hour’s reading. Your future self, three years from now, has none of that. Writing that passes the five-years-from-now test tends to pass every shorter horizon too.

Trust the compound effect, not the day’s output. A single day’s work on the vault looks like very little. A year’s work looks like a full-time research assistant that never sleeps. The gap between those perspectives is where most people give up; don’t.

---

[← Onboarding Guide](10-onboarding-guide.md) · [Docs index](README.md) · [Common Mistakes and Anti-Patterns →](12-common-mistakes-and-anti-patterns.md)
